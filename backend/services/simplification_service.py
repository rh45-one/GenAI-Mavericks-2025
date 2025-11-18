"""LLM-based simplification of legal text."""
from __future__ import annotations

from typing import List, Optional

from .. import schemas
from ..clients.llm_client import LLMClient


class SimplificationService:
    """Provide branches for the two high-level document families."""

    def __init__(self, client: LLMClient):
        self._client = client

    # ---------------------------------------------------------------
    # CONDUCTOR PRINCIPAL: decide qué estrategia usar según el tipo
    # ---------------------------------------------------------------
    def simplify(
        self,
        segmented_document: schemas.SegmentedDocument,
        classification: schemas.ClassificationResult,
    ) -> schemas.SimplificationResult:
        """
        Punto de entrada unificado:
        - Si es RESOLUCION_JURIDICA → simplifyResolution()
        - Si es ESCRITO_PROCESAL → simplifyProceduralWriting()
        - Si es OTRO → intenta simplificación genérica
        """

        doc_type = (classification.docType or "").upper()

        if doc_type == "RESOLUCION_JURIDICA":
            return self.simplifyResolution(segmented_document, classification)

        if doc_type == "ESCRITO_PROCESAL":
            return self.simplifyProceduralWriting(segmented_document, classification)

        # fallback genérico
        return self._genericSimplification(segmented_document, classification)

    # ---------------------------------------------------------------
    # 1) Simplificación de SENTENCIAS, AUTOS, DECRETOS...
    # ---------------------------------------------------------------
    def simplifyResolution(
        self,
        segmented_document: schemas.SegmentedDocument,
        classification: schemas.ClassificationResult,
    ) -> schemas.SimplificationResult:

        text = segmented_document.normalizedText or ""
        doc_type = classification.docType or "RESOLUCION_JURIDICA"
        doc_subtype = classification.docSubtype or "DESCONOCIDO"

        simplified = self._client.callSimplifier(
            text=text,
            doc_type=doc_type,
            doc_subtype=doc_subtype,
        )

        # Podemos identificar secciones destacadas que sean útiles para la guía:
        important_sections = segmented_document.sections or []

        return schemas.SimplificationResult(
            simplifiedText=simplified.strip(),
            importantSections=important_sections,
            docType=doc_type,
            docSubtype=doc_subtype,
        )

    # ---------------------------------------------------------------
    # 2) Simplificación de DEMANDAS, RECURSOS, ESCRITOS DE ALEGACIONES...
    # ---------------------------------------------------------------
    def simplifyProceduralWriting(
        self,
        segmented_document: schemas.SegmentedDocument,
        classification: schemas.ClassificationResult,
    ) -> schemas.SimplificationResult:

        text = segmented_document.normalizedText or ""
        doc_type = classification.docType or "ESCRITO_PROCESAL"
        doc_subtype = classification.docSubtype or "DESCONOCIDO"

        simplified = self._client.callSimplifier(
            text=text,
            doc_type=doc_type,
            doc_subtype=doc_subtype,
        )

        return schemas.SimplificationResult(
            simplifiedText=simplified.strip(),
            importantSections=segmented_document.sections or [],
            docType=doc_type,
            docSubtype=doc_subtype,
        )

    # ---------------------------------------------------------------
    # 3) Fallback genérico por si el documento no está clasificado
    # ---------------------------------------------------------------
    def _genericSimplification(
        self,
        segmented_document: schemas.SegmentedDocument,
        classification: schemas.ClassificationResult,
    ) -> schemas.SimplificationResult:

        text = segmented_document.normalizedText or ""

        simplified = self._client.callSimplifier(
            text=text,
            doc_type="OTRO",
            doc_subtype="DESCONOCIDO",
        )

        return schemas.SimplificationResult(
            simplifiedText=simplified.strip(),
            importantSections=segmented_document.sections or [],
            docType=classification.docType or "OTRO",
            docSubtype=classification.docSubtype or "DESCONOCIDO",
        )
