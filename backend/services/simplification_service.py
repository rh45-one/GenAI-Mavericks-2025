"""LLM-based simplification of legal text (structured textual output)."""
from __future__ import annotations

from typing import List, Tuple, Dict, Any
import re

from .. import schemas
from ..clients.llm_client import BaseLLMClient, LLMClientError
from ..prompt_templates import simplification as simplification_prompt


class SimplificationService:
    """
    Chunk long documents, feed rich context (metadata/parties/falloLiteral) to the LLM,
    and build a structured SimplificationResult while keeping simplifiedText backward-compatible.
    """

    MAX_CHARS = 12000  # soft limit per chunk
    HARD_LIMIT = 16000  # hard emergency limit per chunk

    def __init__(self, client: BaseLLMClient):
        self._client = client

    def simplify(
        self,
        document: schemas.SegmentedDocument,
        classification: schemas.ClassificationResult,
    ) -> schemas.SimplificationResult:
        """Simplify a document using LLM with strong fallo literal constraints."""
        full_text = document.normalizedText or ""
        doc_type = classification.docType or "OTRO"
        doc_subtype = classification.docSubtype or "DESCONOCIDO"
        strategy = self._select_strategy(doc_type, doc_subtype)

        fallo_literal = getattr(document, "falloLiteral", None) or getattr(document, "fallbackFallo", None)
        chunks, truncated = self._build_chunks(full_text, document)

        metadata = self._collect_metadata(document)
        parties = self._collect_parties(document)

        # Prepend fallo chunk for stronger grounding
        if fallo_literal and fallo_literal not in chunks:
            chunks = [fallo_literal] + chunks

        simplified_parts: List[str] = []
        for chunk in chunks:
            part = self._simplify_chunk(
                chunk,
                doc_type,
                doc_subtype,
                fallo_literal=fallo_literal,
                metadata=metadata,
                parties=parties,
            )
            if part:
                simplified_parts.append(part.strip())

        combined_text = "\n\n".join(p for p in simplified_parts if p)
        combined_text = self._remove_meta_comments(combined_text).strip()

        important_sections = self._important_sections(document)

        warnings: List[str] = []
        if truncated:
            warnings.append("El documento fue dividido y truncado parcialmente para poder simplificarlo.")

        return schemas.SimplificationResult(
            simplifiedText=combined_text,
            docType=doc_type,
            docSubtype=doc_subtype,
            importantSections=important_sections,
            strategy=strategy,
            provider=self._client.provider_name,
            truncated=truncated,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Chunking helpers
    # ------------------------------------------------------------------
    def _build_chunks(
        self,
        text: str,
        document: schemas.SegmentedDocument,
    ) -> Tuple[List[str], bool]:
        """Build chunks respecting document structure and limits."""
        if len(text) <= self.MAX_CHARS:
            return [text], False

        chunks: List[str] = []
        truncated = False

        if document.sections:
            for section in document.sections:
                sec_text = (section.content or "").strip()
                if not sec_text:
                    continue
                if len(sec_text) <= self.MAX_CHARS:
                    chunks.append(sec_text)
                else:
                    chunks.extend(self._split_by_paragraphs(sec_text))
        else:
            chunks = self._split_by_paragraphs(text)

        safe_chunks: List[str] = []
        for c in chunks:
            if len(c) > self.HARD_LIMIT:
                safe_chunks.append(c[: self.HARD_LIMIT])
                truncated = True
            else:
                safe_chunks.append(c)

        return safe_chunks, truncated

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Split text by paragraphs trying to respect MAX_CHARS per chunk."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return [text]

        chunks: List[str] = []
        buffer = ""

        for p in paragraphs:
            candidate_len = len(buffer) + len(p) + (2 if buffer else 0)
            if candidate_len <= self.MAX_CHARS:
                buffer = f"{buffer}\n\n{p}" if buffer else p
            else:
                if buffer:
                    chunks.append(buffer)
                buffer = p

        if buffer:
            chunks.append(buffer)

        return chunks

    # ------------------------------------------------------------------
    # LLM invocation per chunk
    # ------------------------------------------------------------------
    def _simplify_chunk(
        self,
        chunk: str,
        doc_type: str,
        doc_subtype: str,
        fallo_literal: str | None = None,
        metadata: Dict[str, str] | None = None,
        parties: Dict[str, str] | None = None,
    ) -> str:
        """Simplify a single chunk via client or prompt, returning structured text."""
        prompt_metadata = metadata or {}
        prompt_parties = parties or {}

        if hasattr(self._client, "simplify") and callable(getattr(self._client, "simplify")):
            try:
                return self._client.simplify(chunk, doc_type, doc_subtype)
            except Exception:
                pass

        system = simplification_prompt.system_prompt()
        user = simplification_prompt.user_prompt(
            chunk,
            doc_type=doc_type,
            doc_subtype=doc_subtype,
            fallo_literal=fallo_literal,
            metadata=prompt_metadata,
            parties=prompt_parties,
        )

        try:
            raw = self._client.chat(system, user, temperature=0.3)
            return raw
        except LLMClientError:
            return chunk
        except Exception:
            return chunk

    # ------------------------------------------------------------------
    # Post-processing helpers
    # ------------------------------------------------------------------
    def _remove_meta_comments(self, text: str) -> str:
        """
        Remove common meta-comments if the model adds them.
        """
        if not text:
            return ""

        META_PATTERNS = [
            "este texto es una version",
            "explicacion simplificada",
            "para conocer el resultado",
            "nota:",
        ]

        lines = text.splitlines()
        cleaned: List[str] = []
        for ln in lines:
            low = ln.lower()
            if any(pat in low for pat in META_PATTERNS):
                continue
            cleaned.append(ln)

        out_lines: List[str] = []
        prev_blank = False
        for ln in cleaned:
            is_blank = not ln.strip()
            if is_blank and prev_blank:
                continue
            out_lines.append(ln)
            prev_blank = is_blank

        return "\n".join(out_lines).strip()

    # ------------------------------------------------------------------
    # Strategy + important sections
    # ------------------------------------------------------------------
    @staticmethod
    def _select_strategy(doc_type: str, doc_subtype: str) -> str:
        doc_type_u = (doc_type or "").upper()
        doc_subtype_u = (doc_subtype or "").upper()

        if doc_type_u == "RESOLUCION_JURIDICA":
            if doc_subtype_u in {"SENTENCIA", "AUTO", "DECRETO"}:
                return "resolution"
            return "resolution_generic"

        if doc_type_u == "ESCRITO_PROCESAL":
            if doc_subtype_u in {"DEMANDA", "RECURSO"}:
                return "procedural_filing"
            return "procedural_generic"

        return "generic"

    @staticmethod
    def _important_sections(document: schemas.SegmentedDocument) -> List[schemas.DocumentSection]:
        """Select the most relevant sections for downstream steps."""
        if not document.sections:
            return []

        sections = document.sections
        name_to_sections = {}
        for sec in sections:
            name_to_sections.setdefault((sec.name or "").upper(), sec)

        priority = [
            "ENCABEZADO",
            "ANTECEDENTES DE HECHO",
            "FUNDAMENTOS DE DERECHO",
            "FUNDAMENTOS JURIDICOS",
            "FALLO",
            "PETICIONES",
        ]

        selected: List[schemas.DocumentSection] = []

        for key in priority:
            sec = name_to_sections.get(key)
            if sec and sec not in selected:
                selected.append(sec)
            if len(selected) >= 4:
                break

        if len(selected) < 3:
            for sec in sections:
                if sec not in selected:
                    selected.append(sec)
                if len(selected) >= 3:
                    break

        return selected

    # ------------------------------------------------------------------
    # Decision helpers
    # ------------------------------------------------------------------
    def _derive_decision_from_fallo(self, fallo_literal: str | None) -> Dict[str, str]:
        if not fallo_literal:
            return {
                "who_wins": "desconocido",
                "costs": "desconocido",
                "plain_text": "No se ha localizado la parte dispositiva (fallo) en este documento.",
                "fallo_literal": "",
            }

        upper = fallo_literal.upper()
        who = "desconocido"
        if "ESTIMA PARCIAL" in upper:
            who = "parcial"
        elif "ESTIMA LA DEMANDA" in upper or "SE ESTIMA" in upper:
            who = "actora"
        elif "DESESTIMA" in upper or "SE DESESTIMA" in upper:
            who = "demandado"

        costs = "desconocido"
        if "COSTAS A LA PARTE ACTORA" in upper:
            costs = "actora"
        elif "COSTAS A LA PARTE DEMANDADA" in upper:
            costs = "demandado"
        elif "SIN HACER ESPECIAL PRONUNCIAMIENTO SOBRE COSTAS" in upper:
            costs = "sin_costas"

        return {
            "who_wins": who,
            "costs": costs,
            "plain_text": fallo_literal.strip(),
            "fallo_literal": fallo_literal.strip(),
        }

    def _collect_metadata(self, document: schemas.SegmentedDocument) -> Dict[str, str]:
        meta = {}
        try:
            extra = getattr(document.metadata, "extra", {}) if document.metadata else {}
            meta["courtName"] = extra.get("courtName", "")
            meta["city"] = extra.get("city", "")
            meta["decisionDate"] = extra.get("decisionDate", "")
            meta["caseNumber"] = extra.get("caseNumber", "")
            meta["judgeName"] = extra.get("judgeName", "")
        except Exception:
            pass
        return meta

    def _collect_parties(self, document: schemas.SegmentedDocument) -> Dict[str, str]:
        parties: Dict[str, str] = {"plaintiffName": "", "defendantName": ""}
        try:
            extra = getattr(document.metadata, "extra", {}) if document.metadata else {}
            parties["plaintiffName"] = extra.get("plaintiffName", "")
            parties["defendantName"] = extra.get("defendantName", "")
        except Exception:
            pass
        return parties
