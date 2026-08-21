"""Basic logging configuration for the TTS system"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name

    Args:
        name (str): The name of the logger

    Returns:
        logging.Logger: The logger instance
    """
    return logging.getLogger(name)