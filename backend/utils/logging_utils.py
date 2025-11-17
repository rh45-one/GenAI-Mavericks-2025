"""Logging utilities for pipeline observability."""
from __future__ import annotations

import logging
import sys
from typing import Final, Optional

# Define a root name for all application loggers
APP_LOGGER_NAME: Final[str] = "justicia_clara_ia"

def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with a standard formatter."""
    
    logger = logging.getLogger(APP_LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)

    if not logger.handlers:
        logger.addHandler(console_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a module-specific or main application logger."""
    if name:
        return logging.getLogger(f"{APP_LOGGER_NAME}.{name}")
    else:
        return logging.getLogger(APP_LOGGER_NAME)
