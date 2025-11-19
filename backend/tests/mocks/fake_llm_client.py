"""Test-only Fake LLM client used by unit tests and mock runners.

Keep this file under tests/mocks so it is explicitly test-only and not used
by production code.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from backend import schemas
from backend.clients.llm_client import BaseLLMClient


class FakeLLMClient(BaseLLMClient):
    @property
    def provider_name(self) -> str:
        return "fake"

    def chat(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        # Very small heuristic-based canned responses for tests
        up = (system_prompt or "") + "\n" + (user_prompt or "")
        low = up.lower()
        if "meaning_for_you" in low or "what_to_do_now" in low or "deadlines_and_risks" in low:
            return json.dumps({
                "meaning_for_you": "Explicación breve para el ciudadano.",
                "what_to_do_now": "Contacte a un abogado.",
                "what_happens_next": "El juzgado tramita la demanda.",
                "deadlines_and_risks": "Plazo principal de 30 días.",
            })
        if "clasifica" in low or "doc_type" in low or "clasificar" in low:
            return json.dumps({
                "doc_type": "RESOLUCION_JURIDICA",
                "doc_subtype": "RECURSO",
                "confidence": 0.9,
                "rationale": "Patrones de recurso identificados",
            })
        if "simplify" in low or "simplificado" in low or "reescribe" in low:
            return json.dumps({"simplified_text": "Texto simplificado de prueba."})
        if "is_safe" in low or "verificador" in low:
            return json.dumps({"is_safe": True, "warnings": [], "verdict": "OK"})

        return json.dumps({"ok": True})

    # Implement abstract convenience methods used by services/tests
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
