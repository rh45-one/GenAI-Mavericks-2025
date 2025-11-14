"""Document ingestion utilities for Justice Made Clear."""
from __future__ import annotations

from .. import schemas


class IngestService:
    """Handle ingestion from text, PDF, or image sources."""

    def fromText(self, document_input: schemas.DocumentInput) -> schemas.IngestResult:
        """Ingest text-based submissions without OCR."""
        # TODO: copy plainText into rawText, capture metadata such as byte length.
        raise NotImplementedError

    def fromPdf(self, document_input: schemas.DocumentInput) -> schemas.IngestResult:
        """Use OCRService.extractTextFromPdf when necessary."""
        # TODO: stream fileContent to OCR client, handle multiple pages.
        raise NotImplementedError

    def fromImage(self, document_input: schemas.DocumentInput) -> schemas.IngestResult:
        """Use OCRService.extractTextFromImage for scanned uploads."""
        # TODO: pass resolution hints, detect language for better OCR accuracy.
        raise NotImplementedError
