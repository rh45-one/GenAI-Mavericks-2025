"""Mock test runner that exercises pipeline without calling external LLM.

This creates a FakeLLMClient that returns deterministic JSON for each
service call. Use it to validate parsing, pydantic models and assembly logic.
"""
from __future__ import annotations

import json
from typing import Any, Dict

import os
import sys

# Ensure repo root is importable when running this script directly
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend import schemas
from backend.services.simplification_service import SimplificationService
from backend.services.classification_service import ClassificationService
from backend.services.legal_guide_service import LegalGuideService
from backend.services.safety_check_service import SafetyCheckService
from backend.clients.llm_client import BaseLLMClient
from backend.prompt_templates import legal_guide as legal_guide_prompt
from backend.prompt_templates import classification as classification_prompt
from backend.prompt_templates import simplification as simplification_prompt


class FakeLLMClient(BaseLLMClient):
    def __init__(self, settings: Dict[str, Any] | None = None):
        super().__init__(settings or {})

    @property
    def provider_name(self) -> str:
        return "fake"

    def chat(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        # Use system vs user prompts to disambiguate intent
        sys_low = (system_prompt or "").lower()
        user_low = (user_prompt or "").lower()

        # Guide generation triggers: system or user mention the guide keys or "texto simplificado"
        if (
            "meaning_for_you" in sys_low
            or "meaning_for_you" in user_low
            or "texto simplificado" in user_low
            or "guia" in sys_low
        ):
            return json.dumps({
                "meaning_for_you": "Esto significa que puede reclamar la nulidad de la cláusula.",
                "what_to_do_now": "Contacte a un abogado y prepare la demanda.",
                "what_happens_next": "El juzgado puede admitir o rechazar la demanda y abrir prueba.",
                "deadlines_and_risks": "Plazo principal: 30 días para interponer recurso; riesgo de prescripción.",
            })

        # Classification triggers: system explicitly instructs to classify or user asks to classify
        if "clasific" in sys_low or "clasific" in user_low or "analiza el siguiente texto" in user_low:
            return json.dumps({
                "doc_type": "RESOLUCION_JURIDICA",
                "doc_subtype": "RECURSO",
                "confidence": 0.92,
                "rationale": "Documento de recurso, lenguaje y estructura característicos",
            })

        # Simplification triggers
        if "reescribe" in sys_low or "reescribe" in user_low or "simplific" in sys_low or "simplific" in user_low:
            return json.dumps({"simplified_text": "Texto simplificado de ejemplo. Mantiene plazos y importes."})
        if "is_safe" in up or "verificador" in up or "verifier" in up:
            return json.dumps({"is_safe": True, "warnings": [], "verdict": "OK"})

        # default: return a simple JSON object
        return json.dumps({"ok": True})

    # Implement abstract methods used elsewhere (some code paths call these)
    def classify(self, text: str, sections=None) -> schemas.ClassificationResult:
        payload = json.loads(self.chat("", "clasifica", 0.0))
        return schemas.ClassificationResult(
            docType=payload.get("doc_type", "OTRO").upper(),
            docSubtype=payload.get("doc_subtype", "DESCONOCIDO").upper(),
            confidence=float(payload.get("confidence", 0.5)),
            source="FAKE",
            explanations=[payload.get("rationale", "")],
        )

    def simplify(self, text: str, doc_type: str, doc_subtype: str) -> str:
        payload = json.loads(self.chat("", "simplify", 0.3))
        return payload.get("simplified_text", "")

    def generate_guide(self, simplified_text: str, context: Dict[str, Any]) -> schemas.LegalGuide:
        payload = json.loads(self.chat("", "meaning_for_you", 0.2))
        return schemas.LegalGuide(
            meaningForYou=payload.get("meaning_for_you", ""),
            whatToDoNow=payload.get("what_to_do_now", ""),
            whatHappensNext=payload.get("what_happens_next", ""),
            deadlinesAndRisks=payload.get("deadlines_and_risks", ""),
            provider=self.provider_name,
        )

    def verify_safety(self, original_text: str, simplified_text: str, legal_guide: schemas.LegalGuide) -> Dict[str, Any]:
        return json.loads(self.chat("", "is_safe", 0.0))


def run_mock():
    # Build minimal input structures
    doc = schemas.SegmentedDocument(rawText="Texto original de prueba.", normalizedText="Texto original de prueba.", sections=[])

    client = FakeLLMClient({})
    # Use realistic thresholds so the LLM fallback may be exercised in the mock
    classification_service = ClassificationService(client, rule_threshold=0.8, force_llm_threshold=0.4)
    simplification_service = SimplificationService(client)
    legal_service = LegalGuideService(client)
    safety_service = SafetyCheckService(client)

    # Debug classification raw payload
    c_system = classification_prompt.system_prompt()
    c_user = classification_prompt.user_prompt(doc.normalizedText[:6000], [])
    print("DEBUG raw classification payload:", client.chat(c_system, c_user, temperature=0.0))

    classification = classification_service.classify(doc)

    # Debug simplification raw payload
    s_system = simplification_prompt.system_prompt()
    s_user = simplification_prompt.user_prompt(doc.normalizedText, doc_type=classification.docType, doc_subtype=classification.docSubtype)
    print("DEBUG raw simplification payload:", client.chat(s_system, s_user, temperature=0.3))

    simplification = simplification_service.simplify(doc, classification)

    # Debug: inspect what the client.chat returns for the legal guide prompt
    system = legal_guide_prompt.system_prompt()
    user = legal_guide_prompt.user_prompt(simplification.simplifiedText, {"doc_type": classification.docType})
    raw_guide = client.chat(system, user, temperature=0.2)
    print("DEBUG raw guide payload:", raw_guide)

    guide = legal_service.build_guide(doc, classification, simplification)
    safety = safety_service.evaluate(doc, simplification, guide)

    response = schemas.ProcessDocumentResponse(
        docType=classification.docType,
        docSubtype=classification.docSubtype,
        simplifiedText=simplification.simplifiedText if hasattr(simplification, 'simplifiedText') else str(simplification),
        legalGuide=guide,
        warnings=[issue.message for issue in safety.issues],
    )

    out = response.model_dump() if hasattr(response, "model_dump") else response.dict()
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run_mock()
