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
            # Prefer high-level generate_guide if available (test fakes)
            if hasattr(self._client, "generate_guide") and callable(getattr(self._client, "generate_guide")):
                res = self._client.generate_guide(simplification_result.simplifiedText, context)
                if isinstance(res, schemas.LegalGuide):
                    return res
                # If client returned dict-like, normalize below
                data = res
            else:
                system = legal_guide_prompt.system_prompt()
                user = legal_guide_prompt.user_prompt(simplification_result.simplifiedText, context)
                raw = self._client.chat(system, user, temperature=0.2)
                try:
                    data = self._client._parse_json(raw)
                except LLMClientError:
                    # Fallback generic guide
                    return schemas.LegalGuide(
                        meaningForYou="No se ha podido generar la guía.",
                        whatToDoNow="",
                        whatHappensNext="",
                        deadlinesAndRisks="",
                        provider=self._client.provider_name,
                    )
        except LLMClientError as exc:
            raise RuntimeError(f"Legal guide generation failed: {exc}") from exc

        # Accept different key styles from the model (snake_case or camelCase)
        def _pick(*keys, default=""):
            for k in keys:
                if k in data and data[k]:
                    return data[k]
            return default

        meaning = _pick("meaning_for_you", "meaningForYou", "meaning", default="")
        todo = _pick("what_to_do_now", "whatToDoNow", "next_steps", default="")
        next_ = _pick("what_happens_next", "whatHappensNext", "what_happens", default="")
        deadlines = _pick("deadlines_and_risks", "deadlinesAndRisks", "risks", default="")

        return schemas.LegalGuide(
            meaningForYou=meaning,
            whatToDoNow=todo,
            whatHappensNext=next_,
            deadlinesAndRisks=deadlines,
            provider=self._client.provider_name,
        )
