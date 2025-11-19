"""LLM-powered classification of legal documents."""
from __future__ import annotations

from typing import List, Optional

from .. import schemas
from ..clients.llm_client import LLMClient


class ClassificationService:
    """Call the LLM to categorize the document type and subtype."""

    def __init__(self, client: LLMClient):
        self._client = client

    def classifyWithLLM(
        self,
        segmented_document: schemas.SegmentedDocument,
    ) -> schemas.ClassificationResult:
        """
        Classify a normalized + segmented document using the LLM.

        - Usa segmented_document.normalizedText como texto principal.
        - Usa segmented_document.sections (list[str]) como contexto opcional.
        - Llama a LLMClient.callClassifier.
        - Aplica una pequeña regla de coherencia para SENTENCIA/AUTO/etc.
        """

        # 1) Texto principal: lo que haya en normalizedText (o cadena vacía)
        text = segmented_document.normalizedText or ""

        # 2) Nombres de secciones (ya son list[str] según tu schema)
        section_names: Optional[List[str]] = segmented_document.sections or None

        # 3) Llamada al LLM (tu LLMClient habla con DeepSeek y tiene heurísticas)
        try:
            llm_output = self._client.callClassifier(
                text=text,
                sections=section_names,
            )
        except Exception as e:
            # Fallback si DeepSeek falla o devuelve error
            return schemas.ClassificationResult(
                docType="OTRO",
                docSubtype="DESCONOCIDO",
                confidence=0.0,
                # rawResponse no existe en el schema actual, así que lo omitimos
            )

        # 4) Normalizamos la salida del LLM
        doc_type = str(llm_output.get("doc_type", "OTRO") or "OTRO").upper()
        doc_subtype = str(llm_output.get("doc_subtype", "DESCONOCIDO") or "DESCONOCIDO").upper()
        try:
            confidence = float(llm_output.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0

        # 5) Regla de coherencia: SENTENCIA/AUTO/etc. → RESOLUCION_JURIDICA
        if (
            doc_subtype in {"SENTENCIA", "AUTO", "DECRETO", "PROVIDENCIA"}
            and doc_type == "ESCRITO_PROCESAL"
        ):
            doc_type = "RESOLUCION_JURIDICA"
            confidence = max(confidence, 0.8)

        # 6) Devolvemos con los nombres de campo REALES del schema
        return schemas.ClassificationResult(
            docType=doc_type,
            docSubtype=doc_subtype,
            confidence=confidence,
        )
