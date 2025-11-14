"""Parsing helpers for dates, deadlines, and monetary amounts."""
from __future__ import annotations

from typing import List


def extract_dates(text: str) -> List[str]:
    """Return normalized date strings found in the text."""
    # TODO: support Spanish month names and ordinal phrases.
    raise NotImplementedError


def extract_deadlines(text: str) -> List[str]:
    """Detect deadline expressions like 'dentro de 5 días'."""
    # TODO: convert expressions into structured durations when possible.
    raise NotImplementedError


def extract_amounts(text: str) -> List[str]:
    """Pull currency or numeric obligations from the document."""
    # TODO: handle COP amounts with punctuation variations.
    raise NotImplementedError
