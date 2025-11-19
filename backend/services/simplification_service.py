"""LLM-based simplification of legal text."""
from __future__ import annotations

from typing import List

from .. import schemas
from ..clients.llm_client import BaseLLMClient, LLMClientError
from ..prompt_templates import simplification as simplification_prompt
import json
import re


class SimplificationService:
    """Provide branches for the two high-level document families."""

    def __init__(self, client: BaseLLMClient):
        self._client = client

    def simplify(
        self,
        document: schemas.SegmentedDocument,
        classification: schemas.ClassificationResult,
    ) -> schemas.SimplificationResult:
        """Entry point selecting the right simplification strategy."""
        doc_type = classification.docType
        doc_subtype = classification.docSubtype

        strategy = self._select_strategy(doc_type, doc_subtype)
        input_text = document.normalizedText
        truncated = False
        max_chars = 12000
        if len(input_text) > max_chars:
            input_text = input_text[:max_chars]
            truncated = True

        try:
            # Prefer the high-level `simplify` if provided by the client (test fakes).
            if hasattr(self._client, "simplify") and callable(getattr(self._client, "simplify")):
                raw_text = self._client.simplify(input_text, doc_type, doc_subtype)
                simplified_text = raw_text or ""
            else:
                system = simplification_prompt.system_prompt()
                user = simplification_prompt.user_prompt(input_text, doc_type=doc_type, doc_subtype=doc_subtype)
                raw = self._client.chat(system, user, temperature=0.3)
                data = self._client._parse_json(raw)
                simplified_text = data.get("simplified_text", "")
        except LLMClientError as exc:
            raise RuntimeError(f"Simplification failed: {exc}") from exc

        # Post-process: remove meta-comments that the prompt prohibits (e.g., lines
        # starting with 'Nota:', or phrases like 'Este es un resumen', or asks to
        # consult the full text). Keep the rest intact.
        def _remove_meta_comments(s: str) -> str:
            if not s:
                return s
            lines = s.splitlines()
            cleaned: list[str] = []
            meta_patterns = [
                re.compile(r"^\s*NOTA\s*[:\-]", re.IGNORECASE),
                re.compile(r"^\s*ESTE ES UN RESUMEN", re.IGNORECASE),
                re.compile(r"CONSULTA[\s\w]*EL TEXTO COMPLETO", re.IGNORECASE),
                re.compile(r"^\s*(PARA DETALLES|CONSULTE)", re.IGNORECASE),
                # Catch 'Nota importante:', 'Nota aclaratoria:', or any line
                # that begins with 'Nota' followed by words and a colon.
                re.compile(r"^\s*NOTA\b", re.IGNORECASE),
                # Remove common footers or italic-marked notes starting with '*'
                re.compile(r"^\s*\*+", re.IGNORECASE),
            ]
            for ln in lines:
                skip = False
                for pat in meta_patterns:
                    if pat.search(ln):
                        skip = True
                        break
                if not skip:
                    cleaned.append(ln)
            # Collapse multiple blank lines
            out_lines = []
            prev_blank = False
            for ln in cleaned:
                is_blank = not ln.strip()
                if is_blank and prev_blank:
                    continue
                out_lines.append(ln)
                prev_blank = is_blank
            return "\n".join(out_lines).strip()

        simplified_text = _remove_meta_comments(simplified_text).strip()

        important_sections = self._important_sections(document)

        warnings = []
        if truncated:
            warnings.append("El documento se trunco para simplificar.")

        return schemas.SimplificationResult(
            simplifiedText=simplified_text.strip(),
            docType=doc_type,
            docSubtype=doc_subtype,
            importantSections=important_sections,
            strategy=strategy,
            provider=self._client.provider_name,
            truncated=truncated,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _select_strategy(doc_type: str, doc_subtype: str) -> str:
        doc_type = doc_type.upper()
        doc_subtype = doc_subtype.upper()

        if doc_type == "RESOLUCION_JURIDICA":
            if doc_subtype in {"SENTENCIA", "AUTO", "DECRETO"}:
                return "resolution"
            return "resolution_generic"
        if doc_type == "ESCRITO_PROCESAL":
            if doc_subtype in {"DEMANDA", "RECURSO"}:
                return "procedural_filing"
            return "procedural_generic"
        return "generic"

    @staticmethod
    def _important_sections(document: schemas.SegmentedDocument) -> List[schemas.DocumentSection]:
        if not document.sections:
            return []
        # Keep up to the first three sections as context for downstream prompts.
        return document.sections[:3]
