"""CLI entrypoint for running the TTS Unix socket server."""

import argparse
import asyncio
from pathlib import Path

from pydantic import ValidationError

from .logging import get_logger
from .models import TTSConfig
from .server import TTSSocketServer

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="jerry-bot-tts",
        description="Run the jerry-bot TTS Unix socket daemon.",
    )

    parser.add_argument(
        "--socket-path",
        type=Path,
        required=True,
        help="Path to the Unix socket file.",
    )
    parser.add_argument(
        "--write-path",
        type=Path,
        required=True,
        help="Directory where generated audio files are written.",
    )

    parser.add_argument(
        "--lang-code",
        required=True,
        help="Language code passed to Kokoro's KPipeline.",
    )
    parser.add_argument(
        "--default-speed",
        type=float,
        default=TTSConfig.model_fields["default_speed"].default,
        help="Default speaking speed when a request does not override it.",
    )
    parser.add_argument(
        "--default-sample-rate",
        type=int,
        default=TTSConfig.model_fields["default_sample_rate"].default,
        help="Sample rate for generated audio.",
    )
    parser.add_argument(
        "--file-extension",
        default=TTSConfig.model_fields["file_extension"].default,
        help="File extension for generated audio files.",
    )

    return parser


async def run_server(socket_path: Path, write_path: Path, config: TTSConfig) -> None:
    """Start and run the Unix socket server forever."""
    write_path.mkdir(parents=True, exist_ok=True)

    if socket_path.exists():
        socket_path.unlink()

    server = TTSSocketServer(
        socket_path=socket_path,
        write_path=write_path,
        tts_config=config,
    )

    socket_server = await asyncio.start_unix_server(
        server.handle_client,
        path=str(socket_path),
    )

    logger.info("Server listening on socket: %s", socket_path)
    async with socket_server:
        await socket_server.serve_forever()


def main() -> int:
    """Parse CLI arguments and run the TTS socket server."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = TTSConfig(
            lang_code=args.lang_code,
            default_speed=args.default_speed,
            default_sample_rate=args.default_sample_rate,
            file_extension=args.file_extension,
        )
    except ValidationError as e:
        parser.error(str(e))

    try:
        asyncio.run(run_server(args.socket_path, args.write_path, config))
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
        return 130
    except OSError as e:
        logger.exception("Failed to start server: %s", e)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
