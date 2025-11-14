"""LLM-based simplification of legal text."""
from __future__ import annotations

from .. import schemas
from ..clients import llm_client


class SimplificationService:
    """Provide branches for the two high-level document families."""

    def __init__(self, client: llm_client.LLMClient):
        self._client = client

    def simplifyResolution(
        self,
        segmented_document: schemas.SegmentedDocument,
        classification: schemas.ClassificationResult,
    ) -> schemas.SimplificationResult:
        """Generate plain-language explanations for court resolutions."""
        # TODO: define prompt template highlighting rulings, parties, deadlines.
        raise NotImplementedError

    def simplifyProceduralWriting(
        self,
        segmented_document: schemas.SegmentedDocument,
        classification: schemas.ClassificationResult,
    ) -> schemas.SimplificationResult:
        """Explain procedural writings (petitions, motions) for citizens."""
        # TODO: prompt should surface requests, arguments, and immediate actions.
        raise NotImplementedError
