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

    # Auto-generate the help message from the TTSConfig model
    for field_name, field in TTSConfig.model_fields.items():
        kwargs = {}
        if field.default is not None:
            kwargs["default"] = field.default
        if field.description:
            kwargs["help"] = field.description
        if field.annotation is not None:
            kwargs["type"] = field.annotation
        parser.add_argument(f"--{field_name.replace('_', '-')}", **kwargs)

    return parser


async def run_server(socket_path: Path, write_path: Path, config: TTSConfig) -> None:
    """Start and run the Unix socket server forever."""
    write_path.mkdir(parents=True, exist_ok=True)

    if socket_path.exists():
        socket_path.unlink()

    server = TTSSocketServer(config)

    socket_server = await asyncio.start_unix_server(
        server.handle_client,
        path=str(socket_path),
    )

    logger.info("Server listening on socket: %s", socket_path)
    try:
        async with socket_server:
            await socket_server.serve_forever()
    finally:
        socket_path.unlink(missing_ok=True)


def main() -> int:
    """Parse CLI arguments and run the TTS socket server."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = TTSConfig(
            **{
                field_name: getattr(args, field_name)
                for field_name in TTSConfig.model_fields.keys()
            }
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
