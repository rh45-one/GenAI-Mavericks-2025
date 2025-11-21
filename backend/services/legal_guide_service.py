"""Legal guide generation service using simplified text and optional decision hints."""
from __future__ import annotations

from typing import Any, Dict

from .. import schemas
from ..clients.llm_client import BaseLLMClient, LLMClientError
from ..prompt_templates import legal_guide as legal_guide_prompt


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
        context: Dict[str, Any] = {
            "doc_type": classification.docType,
            "doc_subtype": classification.docSubtype,
        }

        decision = getattr(simplification_result, "decisionFallo", None)
        decision_dict = {}
        if decision:
            decision_dict = {
                "whoWins": getattr(decision, "whoWins", ""),
                "costs": getattr(decision, "costs", ""),
                "plainText": getattr(decision, "plainText", ""),
                "falloLiteral": getattr(decision, "originalFalloQuote", ""),
            }

        meta_dict: Dict[str, str] = {}
        try:
            extra = getattr(document.metadata, "extra", {}) if document.metadata else {}
            meta_dict = {
                "courtName": extra.get("courtName", ""),
                "decisionDate": extra.get("decisionDate", ""),
                "caseNumber": extra.get("caseNumber", ""),
            }
        except Exception:
            meta_dict = {}

        try:
            if hasattr(self._client, "generate_guide") and callable(getattr(self._client, "generate_guide")):
                res = self._client.generate_guide(simplification_result.simplifiedText, {**context, **decision_dict, **meta_dict})
                if isinstance(res, schemas.LegalGuide):
                    return res
                data = res
            else:
                system = legal_guide_prompt.system_prompt()
                user = legal_guide_prompt.user_prompt(
                    simplification_result.simplifiedText, context, decision_dict, meta_dict
                )
                raw = self._client.chat(system, user, temperature=0.2)
                data = self._client._parse_json(raw)
        except LLMClientError:
            return self._fallback(meta_dict)
        except Exception:
            return self._fallback(meta_dict)

        meaning = data.get("meaning_for_you") or data.get("meaningForYou") or ""
        todo = data.get("what_to_do_now") or data.get("whatToDoNow") or ""
        next_ = data.get("what_happens_next") or data.get("whatHappensNext") or ""
        deadlines = data.get("deadlines_and_risks") or data.get("deadlinesAndRisks") or ""

        return schemas.LegalGuide(
            meaningForYou=meaning or "Revisa la resolucion con ayuda profesional para entender sus efectos.",
            whatToDoNow=todo or "Consulta con tu abogado que obligaciones y derechos se derivan del fallo.",
            whatHappensNext=next_ or "Dependiendo del fallo, puede existir recurso; asesora sobre si conviene recurrir.",
            deadlinesAndRisks=deadlines or "No se identifican plazos claros en el fallo; confirma posibles plazos legales generales.",
            provider=self._client.provider_name,
        )

    def _fallback(self, meta: Dict[str, str]) -> schemas.LegalGuide:
        return schemas.LegalGuide(
            meaningForYou="Revisa la resolucion con ayuda profesional para entender sus efectos.",
            whatToDoNow="Consulta con tu abogado que obligaciones y derechos se derivan del fallo.",
            whatHappensNext="Dependiendo del fallo, puede existir recurso; asesora sobre si conviene recurrir.",
            deadlinesAndRisks="No se identifican plazos claros en el fallo; confirma posibles plazos legales generales.",
            provider=self._client.provider_name,
        )
