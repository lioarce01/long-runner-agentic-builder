"""
Structured logging utility for the multi-agent system

Provides consistent logging across all components with
proper formatting and log levels.
"""

import logging
import os
import sys
from typing import Optional


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """
    Setup structured logging for the application

    Args:
        level: Optional log level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging()
        >>> logger.info("Application started")
    """
    # Get log level from env or parameter
    log_level = level or os.getenv("LOG_LEVEL", "INFO")

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout
    )

    # Create application logger
    logger = logging.getLogger("app-builder")
    return logger


# Default logger instance
logger = setup_logging()


__all__ = ["setup_logging", "logger"]
