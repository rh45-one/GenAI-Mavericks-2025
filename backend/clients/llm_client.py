"""LLM client wrapper for Justice Made Clear."""
from __future__ import annotations

from typing import Any, Dict


class LLMClient:
    """Encapsulate all outbound calls to the LLM provider."""

    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        # TODO: configure HTTP clients, API base URLs, auth headers, etc.

    def callClassifier(self, text: str, sections: list[str] | None = None) -> Dict[str, Any]:
        """Classify the document type/subtype and return confidences."""
        # TODO: integrate with actual LLM SDK.
        raise NotImplementedError

    def callSimplifier(self, text: str, doc_type: str, doc_subtype: str) -> str:
        """Simplify the source document based on its classification."""
        # TODO: define prompt templates separately for maintainability.
        raise NotImplementedError

    def callGuideGenerator(self, simplified_text: str, sections: list[str] | None = None) -> Dict[str, str]:
        """Generate the four guide blocks from simplified text and references."""
        # TODO: respect token budgets; consider streaming outputs.
        raise NotImplementedError

    def callVerifier(self, original_text: str, simplified_text: str, legal_guide: Dict[str, str]) -> Dict[str, Any]:
        """Ask the LLM to confirm that critical meaning remains intact."""
        # TODO: ensure prompts highlight deadlines, parties, obligations.
        raise NotImplementedError
