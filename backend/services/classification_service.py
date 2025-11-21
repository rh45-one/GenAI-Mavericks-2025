"""Hybrid classification service for legal documents."""
from __future__ import annotations

from typing import List, Sequence

from .. import schemas
from ..clients.llm_client import BaseLLMClient, LLMClientError
from ..prompt_templates import classification as classification_prompt
import json
import re


TYPE_KEYWORDS = {
    "RESOLUCION_JURIDICA": [
        "SENTENCIA",
        "FALLO",
        "AUTO",
        "DECRETO",
        "RESUELVO",
    ],
    "ESCRITO_PROCESAL": [
        "DEMANDA",
        "ESCRITO",
        "RECURSO",
        "SUPLICO",
        "SOLICITO",
    ],
}

SUBTYPE_KEYWORDS = {
    "SENTENCIA": ["SENTENCIA"],
    "AUTO": ["AUTO"],
    "PROVIDENCIA": ["PROVIDENCIA"],
    "DECRETO": ["DECRETO"],
    "DEMANDA": ["DEMANDA"],
    "RECURSO": ["RECURSO", "RECURR"],
}


class ClassificationService:
    """Combine rule-based heuristics with a pluggable LLM/ML classifier."""

    def __init__(
        self,
        client: BaseLLMClient,
        rule_threshold: float,
        force_llm_threshold: float,
    ):
        self._client = client
        self._rule_threshold = rule_threshold
        self._force_llm_threshold = force_llm_threshold

    def classify(self, document: schemas.SegmentedDocument) -> schemas.ClassificationResult:
        """Return ClassificationResult prioritizing deterministic rules."""
        rule_result = self._rule_based_classification(document)
        if rule_result.confidence >= self._rule_threshold:
            return rule_result

        llm_result = None
        if rule_result.confidence < self._force_llm_threshold:
            llm_result = self._llm_classification(document, rule_result)
        if llm_result is None:
            return rule_result

        if llm_result.confidence > rule_result.confidence:
            combined_explanations = rule_result.explanations + llm_result.explanations
            return schemas.ClassificationResult(
                docType=llm_result.docType,
                docSubtype=llm_result.docSubtype,
                confidence=llm_result.confidence,
                source="HYBRID",
                explanations=combined_explanations,
            )

        return rule_result

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------
    def _rule_based_classification(
        self,
        document: schemas.SegmentedDocument,
    ) -> schemas.ClassificationResult:
        text = (document.normalizedText or "").upper()
        sections = [section.name.upper() for section in document.sections]

        # Inspect header (first few lines) for strong subtype indicators
        # Expand to first 20 lines to catch headers that include 'Sentencia' markers
        header_lines = (document.normalizedText or "").splitlines()[:20]
        header_text = " ".join([ln.strip().upper() for ln in header_lines if ln.strip()])
        forced_subtype: str | None = None
        # Explicit overrides from header patterns
        if re.search(r"\bSENTENCIA\b", header_text):
            forced_subtype = "SENTENCIA"
        elif re.search(r"\bAUTO\b", header_text):
            forced_subtype = "AUTO"
        elif re.search(r"\bDECRETO\b", header_text):
            forced_subtype = "DECRETO"
        elif re.search(r"\bPROVIDENCIA\b", header_text):
            forced_subtype = "PROVIDENCIA"

        type_scores = {key: 0.0 for key in TYPE_KEYWORDS}
        type_matches: List[str] = []

        for doc_type, keywords in TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in text or kw in sections:
                    type_scores[doc_type] += 0.2
                    type_matches.append(f"{doc_type}:{kw}")

        best_type = max(type_scores, key=type_scores.get)
        best_type_score = min(type_scores[best_type], 1.0)

        subtype_scores = {key: 0.0 for key in SUBTYPE_KEYWORDS}
        subtype_matches: List[str] = []
        for subtype, keywords in SUBTYPE_KEYWORDS.items():
            for kw in keywords:
                # Strong signal if keyword appears in the document header
                if kw in header_text:
                    subtype_scores[subtype] += 1.0
                    subtype_matches.append(f"{subtype}:{kw}(header)")
                elif kw in text:
                    subtype_scores[subtype] += 0.25
                    subtype_matches.append(f"{subtype}:{kw}")

        best_subtype = max(subtype_scores, key=subtype_scores.get)
        best_subtype_score = min(subtype_scores[best_subtype], 1.0)

        # If header contained a clear subtype marker, force it (strong deterministic rule)
        if forced_subtype:
            best_subtype = forced_subtype
            best_subtype_score = 1.0
            subtype_matches.insert(0, f"{forced_subtype}:header_override")

        if best_type_score == 0:
            best_type = "OTRO"
        if best_subtype_score == 0:
            best_subtype = "DESCONOCIDO"

        confidence = min(1.0, max(best_type_score, 0.2) + best_subtype_score * 0.5)
        explanations = []
        if type_matches:
            explanations.append(f"Reglas tipo: {', '.join(type_matches[:5])}")
        if subtype_matches:
            explanations.append(f"Reglas subtipo: {', '.join(subtype_matches[:5])}")
        if not explanations:
            explanations.append("No se detectaron patrones fuertes.")

        return schemas.ClassificationResult(
            docType=best_type,
            docSubtype=best_subtype,
            confidence=round(confidence, 2),
            source="RULES_ONLY",
            explanations=explanations,
        )

    # ------------------------------------------------------------------
    # LLM fallback
    # ------------------------------------------------------------------
    def _llm_classification(
        self,
        document: schemas.SegmentedDocument,
        rule_result: schemas.ClassificationResult,
    ) -> schemas.ClassificationResult | None:
        section_names: Sequence[str] | None = [section.name for section in document.sections]
        try:
            # Backwards-compatible: if the client implements a high-level
            # `classify` method, prefer that (used by test fakes). Otherwise
            # fall back to the chat-based prompt flow.
            if hasattr(self._client, "classify") and callable(getattr(self._client, "classify")):
                try:
                    result = self._client.classify(document.normalizedText[:6000], section_names)
                    # If the client returned a ClassificationResult, return it.
                    if isinstance(result, schemas.ClassificationResult):
                        return result
                    # Otherwise, assume it's a dict-like object.
                    data = result
                except Exception:
                    # fall back to chat-based flow below
                        system = classification_prompt.system_prompt()
                        user = classification_prompt.user_prompt(document.normalizedText[:6000], section_names)
                        raw = self._client.chat(system, user, temperature=0.0)
                        data = self._client._parse_json(raw)
            else:
                system = classification_prompt.system_prompt()
                user = classification_prompt.user_prompt(document.normalizedText[:6000], section_names)
                raw = self._client.chat(system, user, temperature=0.0)
                data = self._client._parse_json(raw)
        except (LLMClientError, json.JSONDecodeError, Exception):
            return None

        doc_type = data.get("doc_type", "OTRO")
        doc_subtype = data.get("doc_subtype", "DESCONOCIDO")
        try:
            confidence = float(data.get("confidence", 0.0))
        except Exception:
            confidence = 0.0

        return schemas.ClassificationResult(
            docType=str(doc_type).upper(),
            docSubtype=str(doc_subtype).upper(),
            confidence=min(max(confidence, 0.0), 1.0),
            source="LLM",
            explanations=[data.get("rationale") or data.get("reasoning") or ""],
        )
