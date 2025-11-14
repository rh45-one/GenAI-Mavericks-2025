"""Legal guide generation service."""
from __future__ import annotations

from .. import schemas
from ..clients import llm_client


class LegalGuideService:
    """Create a four-block LegalGuide DTO from simplified content."""

    def __init__(self, client: llm_client.LLMClient):
        self._client = client

    def buildGuide(self, simplification_result: schemas.SimplificationResult) -> schemas.LegalGuide:
        """Call LLMClient.callGuideGenerator with structured context."""
        # TODO: ensure prompts include docType, docSubtype, and critical sections.
        raise NotImplementedError
