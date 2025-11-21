"""Text normalization and sectioning helpers."""
from __future__ import annotations

import re
from typing import Dict, List, Tuple, Optional

from .. import schemas
from ..utils import text_cleaning

SECTION_KEYWORDS: Dict[str, List[str]] = {
    "ENCABEZADO": [
        "JUZGADO",
        "MAGISTRADO",
        "AUDIENCIA PROVINCIAL",
        "TRIBUNAL SUPERIOR",
    ],
    "ANTECEDENTES DE HECHO": ["ANTECEDENTES DE HECHO", "ANTECEDENTES"],
    "FUNDAMENTOS DE DERECHO": ["FUNDAMENTOS DE DERECHO", "FUNDAMENTOS JURIDICOS"],
    "FALLO": ["FALLO", "RESUELVO"],
    "PETICIONES": ["SUPLICO", "SOLICITO", "PETICION"],
}


class NormalizationService:
    """Clean extracted text and produce structured sections."""

    def normalize(self, ingest_result: schemas.IngestResult) -> schemas.SegmentedDocument:
        """Clean OCR output using deterministic rules and detect sections."""
        raw_text = ingest_result.rawText
        if not raw_text:
            raise ValueError("Ingest result is empty.")

        cleaned = text_cleaning.sanitize_characters(raw_text)
        cleaned = text_cleaning.remove_repeated_headers(cleaned)
        cleaned = text_cleaning.normalize_whitespace(cleaned)

        sections = self._segment_sections(cleaned)

        fallo = self.extract_fallo_literal(cleaned)
        if ingest_result.metadata is None:
            ingest_result.metadata = None
        try:
            if ingest_result.metadata is not None:
                extra = getattr(ingest_result.metadata, "extra", None)
                if extra is None:
                    ingest_result.metadata.extra = {}
                if fallo:
                    ingest_result.metadata.extra["falloLiteral"] = fallo
        except Exception:
            pass

        segmented = schemas.SegmentedDocument(
            rawText=raw_text,
            normalizedText=cleaned,
            sections=sections,
            metadata=ingest_result.metadata,
        )
        try:
            setattr(segmented, "falloLiteral", fallo)
        except Exception:
            pass
        return segmented

    def extract_fallo_literal(self, text: str) -> Optional[str]:
        """Heuristically extract the literal FALLO section from the normalized text.

        Returns the raw substring corresponding to the fallо (as-is) or None
        when no clear FALLO section is found.
        """
        if not text:
            return None

        # Look for common uppercase headers that introduce the fallo section.
        # Match words like 'FALLO', 'FALLÓ', 'RESUELVO', or lines that begin with
        # RESUELVO/RESUELVE/SE RESUELVE.
        pattern = re.compile(r"(^|\n)\s*(FALLO|FALL[ÓO]|RESUELVO|RESUELVE|FALLA)[:\s\n]", re.IGNORECASE)
        m = pattern.search(text)
        if not m:
            return None

        start = m.start()

        # Heuristic end: next line that looks like an uppercase section header
        # (e.g., 'FUNDAMENTOS', 'ANEXO', 'FIRMAS'), or end of text.
        end_pattern = re.compile(r"\n\s*[A-ZÁÉÍÓÚÑ\s]{3,40}\s*\n")
        end_match = end_pattern.search(text, pos=m.end())
        end = end_match.start() if end_match else len(text)

        fallo_text = text[start:end].strip()
        return fallo_text or None

    # ------------------------------------------------------------------
    # Section heuristics
    # ------------------------------------------------------------------
    def _segment_sections(self, text: str) -> List[schemas.DocumentSection]:
        """Identify common Spanish legal sections via keyword spotting."""
        if not text:
            return []

        upper = text.upper()
        markers: List[Tuple[int, str]] = []

        for section_name, keywords in SECTION_KEYWORDS.items():
            matches = [upper.find(kw) for kw in keywords if kw in upper]
            matches = [idx for idx in matches if idx >= 0]
            if matches:
                markers.append((min(matches), section_name))

        if not markers:
            return [
                schemas.DocumentSection(
                    name="CUERPO",
                    content=text.strip() or None,
                    confidence=0.3,
                )
            ]

        markers.sort(key=lambda item: item[0])
        sections: List[schemas.DocumentSection] = []

        for idx, (start, name) in enumerate(markers):
            end = markers[idx + 1][0] if idx + 1 < len(markers) else len(text)
            snippet = text[start:end].strip()
            sections.append(
                schemas.DocumentSection(
                    name=name,
                    content=snippet or None,
                    confidence=0.8 if snippet else 0.6,
                )
            )

        return sections
