"""jerry_bot_tts package."""


def main() -> int:
    """Package-level CLI entrypoint."""
    from .cli import main as cli_main

    return cli_main()


__all__ = ["main"]
