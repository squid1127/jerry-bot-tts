"""Main server implementation"""

import asyncio
from pathlib import Path
import json

from .logging import get_logger
from .models import TTSRequest, TTSConfig, TTSResponse
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

    async def generate_sync(self, request: TTSRequest) -> TTSResponse:
        """Generate TTS audio synchronously

        Args:
            request (TTSRequest): The TTS request

        Returns:
            TTSResponse: The TTS response
        """
        # Generate the TTS audio
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
                    request_data = TTSRequest.from_json_bytes(line)
                except ValueError as e:
                    logger.exception(f"Failed to parse TTS request: {e}")
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
                    response = await self.generate_sync(request_data)
                except Exception as e:
                    logger.exception(f"Failed to generate TTS: {e}")
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

    def _parse_request(self, data: bytes) -> TTSRequest:
        """Parse the incoming request data into a TTSRequest object

        Args:
            data (bytes): The incoming request data, as a JSON-encoded bytes object
        """
        try:
            request_dict = json.loads(data.decode())
            return TTSRequest(**request_dict)
        except (json.JSONDecodeError, TypeError) as e:
            logger.exception(f"Failed to parse TTS request: {e}")
            raise ValueError("Invalid request data") from e
