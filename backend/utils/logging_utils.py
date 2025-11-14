"""Logging utilities for pipeline observability."""
from __future__ import annotations

import logging
from typing import Optional


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with JSON or structured formatting."""
    # TODO: integrate correlation IDs per request and structured logging sinks.
    pass


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a module-specific logger with shared configuration."""
    # TODO: inject request context metadata (document id, user id, etc.).
    return logging.getLogger(name)
