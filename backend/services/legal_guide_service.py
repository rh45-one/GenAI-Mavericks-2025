"""Legal guide generation service."""
from __future__ import annotations

from typing import Any, Dict

from .. import schemas
from ..clients.llm_client import BaseLLMClient, LLMClientError
from ..prompt_templates import legal_guide as legal_guide_prompt
import json


class LegalGuideService:
    """Create a four-block LegalGuide DTO from simplified content."""

    def __init__(self, client: BaseLLMClient):
        self._client = client

    def build_guide(
        self,
        document: schemas.SegmentedDocument,
        classification: schemas.ClassificationResult,
        simplification_result: schemas.SimplificationResult,
    ) -> schemas.LegalGuide:
        """Call the provider-specific generator with structured context."""
        context: Dict[str, Any] = {
            "doc_type": classification.docType,
            "doc_subtype": classification.docSubtype,
            "sections": [section.name for section in simplification_result.importantSections],
            "strategy": simplification_result.strategy,
        }

        try:
            system = legal_guide_prompt.system_prompt()
            user = legal_guide_prompt.user_prompt(simplification_result.simplifiedText, context)
            raw = self._client.chat(system, user, temperature=0.2)
            data = json.loads(raw)
        except LLMClientError as exc:
            raise RuntimeError(f"Legal guide generation failed: {exc}") from exc
        except json.JSONDecodeError:
            # Fallback generic guide
            return schemas.LegalGuide(
                meaningForYou="No se ha podido generar la guía.",
                whatToDoNow="",
                whatHappensNext="",
                deadlinesAndRisks="",
                provider=self._client.provider_name,
            )

        return schemas.LegalGuide(
            meaningForYou=data.get("meaning_for_you", ""),
            whatToDoNow=data.get("what_to_do_now", ""),
            whatHappensNext=data.get("what_happens_next", ""),
            deadlinesAndRisks=data.get("deadlines_and_risks", ""),
            provider=self._client.provider_name,
        )
