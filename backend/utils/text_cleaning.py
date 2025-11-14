"""Text cleaning helpers used by normalization service."""
from __future__ import annotations


def normalize_whitespace(text: str) -> str:
    """Collapse extra whitespace and standardize line endings."""
    # TODO: implement actual regex-based cleanup.
    return text


def remove_repeated_headers(text: str) -> str:
    """Strip duplicated court headers common in scanned PDFs."""
    # TODO: inspect heuristics for Colombian and LATAM legal docs.
    return text


def sanitize_characters(text: str) -> str:
    """Remove OCR artifacts (e.g., stray hyphens, ligatures)."""
    # TODO: convert special unicode characters to ASCII equivalents.
    return text
