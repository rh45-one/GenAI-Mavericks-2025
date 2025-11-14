"""Safety verification service to ensure meaning preservation."""
from __future__ import annotations

from .. import schemas
from ..clients import llm_client
from ..utils import date_amount_parsing


class SafetyCheckService:
    """Combine deterministic rules with LLM verification calls."""

    def __init__(self, client: llm_client.LLMClient):
        self._client = client

    def ruleBasedCheck(self, original: schemas.SegmentedDocument, simplified: schemas.SimplificationResult) -> schemas.SafetyCheckResult:
        """Detect missing deadlines, altered amounts, or dropped parties."""
        # TODO: use date_amount_parsing helpers to compare extracted entities.
        raise NotImplementedError

    def llmVerification(
        self,
        original: schemas.SegmentedDocument,
        simplified: schemas.SimplificationResult,
        legal_guide: schemas.LegalGuide,
    ) -> schemas.SafetyCheckResult:
        """Use LLMClient.callVerifier to double-check semantic fidelity."""
        # TODO: merge findings with rule-based results and surface warnings.
        raise NotImplementedError
