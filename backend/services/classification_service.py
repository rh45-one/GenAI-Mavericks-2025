"""LLM-powered classification of legal documents."""
from __future__ import annotations

from .. import schemas
from ..clients import llm_client


class ClassificationService:
    """Call the LLM to categorize the document type and subtype."""

    def __init__(self, client: llm_client.LLMClient):
        self._client = client

    def classifyWithLLM(self, segmented_document: schemas.SegmentedDocument) -> schemas.ClassificationResult:
        """Invoke LLMClient.callClassifier with normalized text and sections."""
        # TODO: craft prompts referencing document structure and fallback heuristics.
        raise NotImplementedError
