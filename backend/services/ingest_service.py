"""Document ingestion utilities for Justice Made Clear."""
from __future__ import annotations

import base64
from typing import Optional, Dict, Any

from .. import schemas
from ..clients.ocr_client import OCRService

class IngestService:
    """Handle ingestion from text, PDF, or image sources."""

    def __init__(self, ocr: Optional[OCRService] = None):
        # Si no pasas un OCRService, te creo uno por defecto.
        self._ocr = ocr or OCRService()

    # ------------------------------------------------------------------
    # 1) TEXT
    # ------------------------------------------------------------------
    def fromText(self, document_input: schemas.DocumentInput) -> schemas.IngestResult:
        """
        Ingest text-based submissions.

        - Copia plainText en rawText.
        - Añade metadatos básicos.
        """
        text = (document_input.plainText or "").strip()

        metadata = {
            "sourceType": "text",
            "length": len(text),
        }

        return schemas.IngestResult(
            rawText=text,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Helper: decodificar base64 si viene así
    # ------------------------------------------------------------------
    def _decode_file(self, fileContent: Optional[str]) -> bytes:
        """
        Devuelve bytes del archivo.

        - Si es None → error.
        - Si no parece base64 → intentar tratarlo como binario en string.
        """
        if not fileContent:
            raise ValueError("fileContent is empty or missing.")

        try:
            # Intentar base64 normal
            return base64.b64decode(fileContent, validate=True)
        except Exception:
            try:
                # Si no era base64 válido, devolver raw bytes del string
                return fileContent.encode("utf-8", errors="ignore")
            except Exception:
                raise ValueError("fileContent could not be decoded as base64 or bytes.")

    # ------------------------------------------------------------------
    # 2) PDF
    # ------------------------------------------------------------------
    def fromPdf(self, document_input: schemas.DocumentInput) -> schemas.IngestResult:
        """
        Handle PDFs:
        - Decodifica fileContent.
        - Extrae texto usando OCRService.extractTextFromPdf.
        - Devuelve IngestResult.
        """
        data_bytes = self._decode_file(document_input.fileContent)

        text = self._ocr.extractTextFromPdf(data_bytes)

        metadata: Dict[str, Any] = {
            "sourceType": "pdf",
            "length": len(text),
        }

        return schemas.IngestResult(
            rawText=text,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # 3) IMAGE
    # ------------------------------------------------------------------
    def fromImage(self, document_input: schemas.DocumentInput) -> schemas.IngestResult:
        """
        Handle images:
        - Decodifica fileContent.
        - Llama a extractTextFromImage.
        - Devuelve IngestResult.
        """
        data_bytes = self._decode_file(document_input.fileContent)

        # Idioma por defecto español ("spa") si quieres mejorar OCR
        text = self._ocr.extractTextFromImage(data_bytes, language="spa")

        metadata: Dict[str, Any] = {
            "sourceType": "image",
            "length": len(text),
        }

        return schemas.IngestResult(
            rawText=text,
            metadata=metadata,
        )