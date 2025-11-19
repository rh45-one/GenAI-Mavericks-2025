"""Provider-agnostic LLM client implementations."""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence

import requests

from .. import schemas

PLACEHOLDER_API_KEY = "sk-df093be9aa194206b0602986351c07c4"


class LLMClientError(RuntimeError):
    """Raised when the LLM provider cannot satisfy a request."""


class BaseLLMClient(ABC):
    """Abstract interface implemented by every model provider."""

    def __init__(self, settings: Dict[str, Any]):
        self._settings = settings

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return a short identifier for the provider (deepseek, openai, local_legal, etc.)."""

    @abstractmethod
    def classify(
        self,
        text: str,
        sections: Sequence[str] | None = None,
    ) -> schemas.ClassificationResult:
        """Classify the document and return docType/docSubtype/confidence."""

    @abstractmethod
    def simplify(self, text: str, doc_type: str, doc_subtype: str) -> str:
        """Return a simplified paraphrase of the supplied document."""

    @abstractmethod
    def generate_guide(
        self,
        simplified_text: str,
        context: Dict[str, Any],
    ) -> schemas.LegalGuide:
        """Generate the standard four-block legal guide."""

    @abstractmethod
    def verify_safety(
        self,
        original_text: str,
        simplified_text: str,
        legal_guide: schemas.LegalGuide,
    ) -> Dict[str, Any]:
        """Return a dict describing potential safety issues."""


class DeepSeekLLMClient(BaseLLMClient):
    """Concrete implementation backed by DeepSeek's OpenAI-compatible API."""

    def __init__(self, settings: Dict[str, Any]):
        super().__init__(settings)
        self._base_url = (settings.get("llm_base_url") or "https://api.deepseek.com").rstrip("/")
        self._model = settings.get("llm_model_name", "deepseek-chat")
        self._api_key = settings.get("llm_api_key") or PLACEHOLDER_API_KEY
        self._timeout = int(settings.get("llm_timeout", 60))
        self._retries = max(1, int(settings.get("llm_retries", 1)))
        self._max_tokens = settings.get("llm_max_tokens")
        self._classification_temperature = float(settings.get("classification_temperature", 0.0))
        self._simplification_temperature = float(settings.get("simplification_temperature", 0.3))
        self._guide_temperature = float(settings.get("guide_temperature", 0.25))
        self._safety_temperature = float(settings.get("safety_temperature", 0.0))

    def chat(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        """Provider-agnostic chat entry used by services with centralized prompts."""
        return self._chat_completion(system_prompt=system_prompt, user_prompt=user_prompt, temperature=temperature)

    @property
    def provider_name(self) -> str:  # pragma: no cover - trivial property
        return "deepseek"

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def classify(
        self,
        text: str,
        sections: Sequence[str] | None = None,
    ) -> schemas.ClassificationResult:
        system_prompt = (
            "Eres un analista jur�dico especializado en documentos espa�oles. "
            "Debes devolver SIEMPRE un JSON estricto con:\n"
            '  {"doc_type": "...", "doc_subtype": "...", "confidence": 0-1, "rationale": "..."}\n'
            "doc_type pertenece a: RESOLUCION_JURIDICA, ESCRITO_PROCESAL, OTRO.\n"
            "doc_subtype pertenece a: SENTENCIA, AUTO, DECRETO, DEMANDA, RECURSO, ESCRITO, DESCONOCIDO."
        )

        context_sections = "\n".join(f"- {name}" for name in sections or [])
        user_prompt = (
            "Clasifica el siguiente documento. Usa m�x 30 palabras en rationale.\n"
            f"Secciones detectadas:\n{context_sections or '- (sin secciones detectadas)'}\n\n"
            f"TEXTO:\n{text[:6000]}"
        )

        payload = self._chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self._classification_temperature,
        )
        data = self._parse_json(payload)

        doc_type = str(data.get("doc_type", "OTRO") or "OTRO").upper()
        doc_subtype = str(data.get("doc_subtype", "DESCONOCIDO") or "DESCONOCIDO").upper()
        try:
            confidence = float(data.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = min(max(confidence, 0.0), 1.0)

        rationale = data.get("rationale") or data.get("reasoning") or ""

        return schemas.ClassificationResult(
            docType=doc_type,
            docSubtype=doc_subtype,
            confidence=confidence,
            source="LLM",
            explanations=[rationale] if rationale else [],
        )

    def simplify(self, text: str, doc_type: str, doc_subtype: str) -> str:
        system_prompt = (
            "Eres un asistente jur�dico que reescribe resoluciones y escritos en lenguaje claro. "
            "Debes mantener plazos, importes y efectos legales. Nunca inventes informaci�n nueva."
        )
        user_prompt = (
            f"Tipo de documento: {doc_type} / {doc_subtype}.\n"
            "Reescribe el texto siguiente en lenguaje claro para un ciudadano sin formaci�n jur�dica.\n"
            "TEXTO:\n"
            f"{text[:8000]}"
        )

        return self._chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self._simplification_temperature,
        ).strip()

    def generate_guide(
        self,
        simplified_text: str,
        context: Dict[str, Any],
    ) -> schemas.LegalGuide:
        system_prompt = (
            "Eres un asistente jur�dico que crea una gu�a para ciudadanos. "
            "Debes responder SIEMPRE en JSON estricto con las claves:\n"
            "meaning_for_you, what_to_do_now, what_happens_next, deadlines_and_risks."
        )
        context_dump = json.dumps(context, ensure_ascii=False, indent=2)
        user_prompt = (
            f"Contexto: {context_dump}\n\n"
            "Redacta la gu�a en frases cortas y accionables usando el texto simplificado como fuente.\n"
            f"TEXTO SIMPLIFICADO:\n{simplified_text[:6000]}"
        )

        payload = self._chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self._guide_temperature,
        )
        data = self._parse_json(payload)

        return schemas.LegalGuide(
            meaningForYou=data.get("meaning_for_you")
            or data.get("meaningForYou")
            or "No se pudo generar la gu�a.",
            whatToDoNow=data.get("what_to_do_now") or data.get("whatToDoNow") or "",
            whatHappensNext=data.get("what_happens_next") or data.get("whatHappensNext") or "",
            deadlinesAndRisks=data.get("deadlines_and_risks")
            or data.get("deadlinesAndRisks")
            or "",
            provider=self.provider_name,
        )

    def verify_safety(
        self,
        original_text: str,
        simplified_text: str,
        legal_guide: schemas.LegalGuide,
    ) -> Dict[str, Any]:
        system_prompt = (
            "Eres un verificador jur�dico. Compara el texto original con el simplificado y la gu�a. "
            "Devuelve JSON estricto con: is_safe (bool), warnings (lista de strings), verdict (string breve)."
        )
        guide_dump = json.dumps(legal_guide.model_dump(), ensure_ascii=False, indent=2)
        user_prompt = (
            f"TEXTO ORIGINAL:\n{original_text[:5000]}\n\n"
            f"TEXTO SIMPLIFICADO:\n{simplified_text[:5000]}\n\n"
            f"GUIA:\n{guide_dump}"
        )

        payload = self._chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self._safety_temperature,
        )
        data = self._parse_json(payload)

        warnings = data.get("warnings")
        if not isinstance(warnings, list):
            warnings = ["El verificador no devolvi� advertencias estructuradas."]

        return {
            "is_safe": bool(data.get("is_safe", False)),
            "warnings": [str(item) for item in warnings],
            "verdict": data.get("verdict") or "",
            "raw_response": payload,
        }

    # ------------------------------------------------------------------
    # HTTP helper
    # ------------------------------------------------------------------
    def _chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ) -> str:
        if not self._api_key or self._api_key == PLACEHOLDER_API_KEY:
            raise LLMClientError(
                "DeepSeek API key missing. Set LLM_API_KEY or DEEPSEEK_API_KEY."
            )

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        if self._max_tokens:
            payload["max_tokens"] = int(self._max_tokens)

        url = f"{self._base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        last_error: Optional[Exception] = None
        for attempt in range(1, self._retries + 1):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self._timeout,
                )
                response.raise_for_status()
                json_payload = response.json()
                choices = json_payload.get("choices") or []
                if not choices:
                    raise LLMClientError("DeepSeek response missing 'choices'.")
                return choices[0]["message"]["content"]
            except Exception as exc:  # pragma: no cover - network failure dependent
                last_error = exc
                if attempt < self._retries:
                    time.sleep(0.25 * attempt)
                continue

        raise LLMClientError(f"DeepSeek request failed: {last_error}")

    @staticmethod
    def _parse_json(payload: str) -> Dict[str, Any]:
        # Tolerant JSON parsing: try direct parse, then extract first {...} object
        if not isinstance(payload, str):
            raise LLMClientError("LLM response was not a string payload")

        p = payload.strip()
        try:
            return json.loads(p)
        except json.JSONDecodeError:
            # Try to extract the first JSON object within the string
            start = p.find("{")
            end = p.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = p[start : end + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    # fall through to error below
                    pass

        # If we reach here, parsing failed — include a short snippet for debugging
        snippet = (p or "")[:600]
        raise LLMClientError(f"LLM response was not valid JSON. Snippet: {snippet}")
