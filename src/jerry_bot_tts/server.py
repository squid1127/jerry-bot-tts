"""Main server implementation"""

import asyncio
import json
from pathlib import Path

from aiofiles import os as aiofiles_os

from .logging import get_logger
from .models import (
    TTSCommand,
    TTSCommandRequest,
    TTSCommandResponse,
    TTSConfig,
    TTSRequest,
    TTSResponse,
)
from .tts import TTS

logger = get_logger(__name__)


class TTSSocketServer:
    """TTS Unix socket server implementation"""

    def __init__(self, config: TTSConfig):
        """Initialize the TTS socket server

        Args:

            config (TTSConfig): The TTS configuration
        """
        self.config = config
        self.tts = TTS(self.config)

        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        self.clean_event: asyncio.Event | None = None

    async def generate_sync(self, request: TTSRequest) -> TTSResponse:
        """Generate TTS audio synchronously

        Args:
            request (TTSRequest): The TTS request

        Returns:
            TTSResponse: The TTS response
        """
        # Generate the TTS audio
        if self.clean_event is not None and not self.clean_event.is_set():
            await self.clean_event.wait()

        async with self.semaphore:
            file = await asyncio.get_event_loop().run_in_executor(
                None,
                self.tts.generate,
                request,
            )

        return TTSResponse(
            type="generate",
            status="success",
            message="TTS generated successfully",
            uuid=request.uuid,
            filename=file.name if file else None,
        )

    async def handle_command(self, request: TTSCommandRequest) -> TTSCommandResponse:
        """Handle TTS command requests

        Args:
            request (TTSCommandRequest): The TTS command request

        Returns:
            TTSCommandResponse: The TTS command response
        """
        if request.command == TTSCommand.PING:
            return TTSCommandResponse(
                command=request.command,
                ok=True,
                uuid=request.uuid,
                message="Pong",
            )
        elif request.command == TTSCommand.CLEAN:
            try:
                await self.clean_audio_files()
                return TTSCommandResponse(
                    command=request.command,
                    ok=True,
                    uuid=request.uuid,
                    message="Audio files cleaned successfully",
                )
            except Exception as e:
                logger.exception("Failed to clean audio files")
                return TTSCommandResponse(
                    command=request.command,
                    ok=False,
                    uuid=request.uuid,
                    message=str(e),
                )
            finally:
                if self.clean_event is not None:
                    self.clean_event.set()

        raise ValueError(f"Unknown command: {request.command}")

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Handle incoming client connections

        Args:
            reader (asyncio.StreamReader): The stream reader for the client connection
            writer (asyncio.StreamWriter): The stream writer for the client connection
        """
        try:
            while line := await reader.readline():
                try:
                    request_data = self._parse_request(line)
                except (ValueError, TypeError) as e:
                    logger.exception("Failed to parse TTS request")
                    response = TTSResponse(
                        type="parse",
                        status="error",
                        uuid=None,
                        message=str(e),
                        filename=None,
                    )
                    writer.write(response.to_json_bytes() + b"\n")
                    await writer.drain()
                    continue
                try:
                    if isinstance(request_data, TTSCommandRequest):
                        response = await self.handle_command(request_data)
                    else:
                        response = await self.generate_sync(request_data)
                except Exception as e:
                    logger.exception("Failed to generate TTS")
                    response = TTSResponse(
                        type="generate",
                        status="error",
                        uuid=request_data.uuid,
                        message=str(e),
                        filename=None,
                    )
                writer.write(response.to_json_bytes() + b"\n")
                await writer.drain()
        finally:
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()

    def _parse_request(self, data: bytes) -> TTSRequest | TTSCommandRequest:
        """Parse the incoming request data into a TTSRequest object

        Args:
            data (bytes): The incoming request data, as a JSON-encoded bytes object
        """
        try:
            request_dict = json.loads(data.decode())
            if not isinstance(request_dict, dict):
                raise TypeError("Request data must be a JSON object")
            if "command" in request_dict:
                return TTSCommandRequest(**request_dict)
            return TTSRequest(**request_dict)
        except (json.JSONDecodeError, TypeError) as e:
            logger.exception("Failed to parse TTS request")
            raise ValueError("Invalid request data") from e

    async def clean_audio_files(self):
        """Clean up generated audio files in the write path"""
        self.clean_event = asyncio.Event()
        try:
            write_path = Path(self.config.write_path)
            if not write_path.exists():
                logger.warning(f"Write path {write_path} does not exist")
                return
            for file in write_path.glob("*.wav"):
                try:
                    await aiofiles_os.remove(file)
                    logger.info(f"Deleted audio file: {file}")
                except Exception:
                    logger.exception(f"Failed to delete audio file {file}")
        finally:
            if self.clean_event is not None:
                self.clean_event.set()