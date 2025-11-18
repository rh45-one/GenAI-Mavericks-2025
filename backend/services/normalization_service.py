"""Text normalization and sectioning helpers."""
from __future__ import annotations

import re
from typing import List

from .. import schemas


class NormalizationService:
    """Clean extracted text and produce structured sections."""

    # ---------------------------------------------------------
    # 1) NORMALIZAR TEXTO
    # ---------------------------------------------------------
    def normalizeText(self, ingest_result: schemas.IngestResult) -> schemas.SegmentedDocument:
        """
        Apply basic cleaning to the raw text:
        - Normaliza saltos de línea (\r\n, \r → \n).
        - Elimina espacios en blanco al inicio/fin de línea.
        - Colapsa líneas vacías múltiples.
        - Deja el texto en normalizedText.
        """
        raw = ingest_result.rawText or ""

        # 1) Normalizar saltos de línea
        text = raw.replace("\r\n", "\n").replace("\r", "\n")

        # 2) Quitar espacios al principio y final de cada línea
        lines: List[str] = [line.strip() for line in text.split("\n")]

        # 3) Colapsar múltiples líneas vacías en una sola
        cleaned_lines: List[str] = []
        empty_streak = 0
        for line in lines:
            if line == "":
                empty_streak += 1
                # Permitimos como mucho una línea vacía seguida
                if empty_streak > 1:
                    continue
            else:
                empty_streak = 0
            cleaned_lines.append(line)

        normalized = "\n".join(cleaned_lines).strip()

        # De momento aún no segmentamos secciones: eso se hace en segmentSections()
        return schemas.SegmentedDocument(
            normalizedText=normalized,
            sections=None,
        )

    # ---------------------------------------------------------
    # 2) DETECTAR SECCIONES (muy simple pero útil)
    # ---------------------------------------------------------
    def segmentSections(self, normalized_document: schemas.SegmentedDocument) -> schemas.SegmentedDocument:
        """
        Detect typical sections (for Spanish court decisions) and store their names in `sections`.

        No troceamos el texto aquí (tu schema solo tiene List[str]), simplemente
        detectamos qué secciones parecen estar presentes en el texto:

        - "ENCABEZADO"
        - "ANTECEDENTES DE HECHO"
        - "FUNDAMENTOS DE DERECHO"
        - "FALLO"
        - etc.
        """
        text = normalized_document.normalizedText or ""
        upper = text.upper()

        possible_sections = {
            "ENCABEZADO": [
                "JUZGADO DE 1ª INSTANCIA",
                "JUZGADO DE PRIMERA INSTANCIA",
                "JUZGADO DE",
                "MAGISTRADO",
                "MAGISTRADA",
            ],
            "ANTECEDENTES DE HECHO": ["ANTECEDENTES DE HECHO"],
            "FUNDAMENTOS DE DERECHO": ["FUNDAMENTOS DE DERECHO"],
            "FUNDAMENTOS JURÍDICOS": ["FUNDAMENTOS JURÍDICOS", "FUNDAMENTOS JURIDICOS"],
            "FALLO": ["FALLO"],
            # Puedes ampliar con más si quieres
        }

        detected: List[str] = []

        for section_name, keywords in possible_sections.items():
            for kw in keywords:
                if kw in upper:
                    detected.append(section_name)
                    break  # no hace falta seguir buscando más keywords de esa sección

        # Eliminamos duplicados manteniendo orden
        seen = set()
        unique_detected: List[str] = []
        for s in detected:
            if s not in seen:
                seen.add(s)
                unique_detected.append(s)

        return schemas.SegmentedDocument(
            normalizedText=normalized_document.normalizedText,
            sections=unique_detected or None,
        )
