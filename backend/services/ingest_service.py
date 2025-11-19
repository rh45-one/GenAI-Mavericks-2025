"""Document ingestion utilities for Justice Made Clear."""
from __future__ import annotations

import base64
from typing import Optional

from .. import schemas
from ..clients.ocr_client import OCRClientError, OCRService


class IngestService:
    """Handle ingestion from text, PDF, or image sources."""

    def __init__(self, ocr: OCRService, default_language: str = "es"):
        self._ocr = ocr
        self._default_language = default_language

    def ingest(self, document_input: schemas.DocumentInput) -> schemas.IngestResult:
        """Public entry point that routes to the correct ingestion strategy."""
        source = (document_input.sourceType or "").lower()
        if source == "text":
            return self._from_text(document_input)
        if source == "pdf":
            return self._from_pdf(document_input)
        if source == "image":
            return self._from_image(document_input)
        raise ValueError(f"Unsupported sourceType '{document_input.sourceType}'.")

    # ------------------------------------------------------------------
    # TEXT INGESTION
    # ------------------------------------------------------------------
    def _from_text(self, document_input: schemas.DocumentInput) -> schemas.IngestResult:
        text = (document_input.plainText or "").strip()
        if not text:
            raise ValueError("plainText is required when sourceType=text.")

        metadata = schemas.DocumentMetadata(
            sourceType="text",
            language=self._default_language,
            charLength=len(text),
            extra={},
        )
        return schemas.IngestResult(rawText=text, metadata=metadata)

    # ------------------------------------------------------------------
    # PDF INGESTION
    # ------------------------------------------------------------------
    def _from_pdf(self, document_input: schemas.DocumentInput) -> schemas.IngestResult:
        data_bytes = self._decode_file(document_input.fileContent)
        try:
            text = self._ocr.extract_text_from_pdf(data_bytes, language=self._default_language)
        except OCRClientError as exc:
            raise ValueError(f"OCR PDF extraction failed: {exc}") from exc

        metadata = schemas.DocumentMetadata(
            sourceType="pdf",
            language=self._default_language,
            charLength=len(text),
            extra={"bytes": str(len(data_bytes))},
        )
        return schemas.IngestResult(rawText=text, metadata=metadata)

    # ------------------------------------------------------------------
    # IMAGE INGESTION
    # ------------------------------------------------------------------
    def _from_image(self, document_input: schemas.DocumentInput) -> schemas.IngestResult:
        data_bytes = self._decode_file(document_input.fileContent)
        try:
            text = self._ocr.extract_text_from_image(data_bytes, language=self._default_language)
        except OCRClientError as exc:
            raise ValueError(f"OCR image extraction failed: {exc}") from exc

        metadata = schemas.DocumentMetadata(
            sourceType="image",
            language=self._default_language,
            charLength=len(text),
            extra={"bytes": str(len(data_bytes))},
        )
        return schemas.IngestResult(rawText=text, metadata=metadata)

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    @staticmethod
    def _decode_file(file_content: Optional[str]) -> bytes:
        if not file_content:
            raise ValueError("fileContent is required for pdf/image ingestion.")

        try:
            return base64.b64decode(file_content, validate=True)
        except Exception:
            return file_content.encode("utf-8", errors="ignore")
