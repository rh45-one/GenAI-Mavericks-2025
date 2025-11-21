"""Lightweight fake LLM client for local development and demos."""
from __future__ import annotations

import json
from typing import Any, Dict, Sequence

from .. import schemas
from .llm_client import BaseLLMClient


class FakeLLMClient(BaseLLMClient):
    """Deterministic responses to keep the pipeline working without an API key."""

    def __init__(self, settings: Dict[str, Any] | None = None):
        super().__init__(settings or {})

    @property
    def provider_name(self) -> str:  # pragma: no cover - simple property
        return "fake"

    # The service layers mostly call these helpers directly. Still keep a chat()
    # implementation so prompt-based code paths also work when needed.
    def chat(self, system_prompt: str, user_prompt: str, temperature: float) -> str:  # pragma: no cover - dev only
        payload = self._build_payload(system_prompt, user_prompt)
        return json.dumps(payload)

    def classify(self, text: str, sections: Sequence[str] | None = None) -> schemas.ClassificationResult:
        return schemas.ClassificationResult(
            docType="RESOLUCION_JURIDICA",
            docSubtype="SENTENCIA",
            confidence=0.9,
            source="FAKE",
            explanations=["Coincidencias de patrones determinísticas."],
        )

    def simplify(self, text: str, doc_type: str, doc_subtype: str) -> str:
        return (
            "Resumen de demostración para el documento proporcionado. "
            "Integre DeepSeek/OpenAI para respuestas reales."
        )

    def generate_guide(self, simplified_text: str, context: Dict[str, Any]) -> schemas.LegalGuide:
        return schemas.LegalGuide(
            meaningForYou="Este es un ejemplo educativo basado en el texto que compartiste.",
            whatToDoNow="Revisa plazos y prepara la documentación necesaria.",
            whatHappensNext="El juzgado notificará los siguientes pasos procesales.",
            deadlinesAndRisks="Asegúrate de responder antes del plazo indicado para evitar sanciones.",
            provider=self.provider_name,
        )

    def verify_safety(
        self,
        original_text: str,
        simplified_text: str,
        legal_guide: schemas.LegalGuide,
    ) -> Dict[str, Any]:
        return {"is_safe": True, "warnings": [], "verdict": "OK"}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _build_payload(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Tiny heuristic to mimic multiple tasks using the chat() interface."""
        lower_payload = f"{system_prompt}\n{user_prompt}".lower()
        if "doc_type" in lower_payload or "clasifica" in lower_payload:
            return {
                "doc_type": "RESOLUCION_JURIDICA",
                "doc_subtype": "SENTENCIA",
                "confidence": 0.9,
                "rationale": "Patrones determinísticos coinciden con una sentencia.",
            }
        if "simplified_text" in lower_payload or "simplify" in lower_payload:
            return {"simplified_text": "Resumen ficticio. Conecta tu LLM para resultados reales."}
        if "meaning_for_you" in lower_payload or "legal guide" in lower_payload:
            return {
                "meaning_for_you": "Este es un ejemplo ficticio del significado principal.",
                "what_to_do_now": "Comunícate con tu abogado o asesor de confianza.",
                "what_happens_next": "El proceso continuará según el procedimiento estándar.",
                "deadlines_and_risks": "Verifica plazos legales para evitar riesgos.",
            }
        if "is_safe" in lower_payload or "warnings" in lower_payload:
            return {"is_safe": True, "warnings": [], "verdict": "Sin alertas."}
        return {"ok": True}
