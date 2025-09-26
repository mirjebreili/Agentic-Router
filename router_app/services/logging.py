"""
Structured logging setup for the application.
"""
import logging
import sys


def setup_logging(name: str) -> logging.Logger:
    """
    Configures and returns a logger with a specified name.

    Args:
        name: The name for the logger, typically __name__.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger