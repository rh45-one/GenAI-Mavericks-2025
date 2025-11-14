"""OCR client wrapper for Justice Made Clear."""
from __future__ import annotations

from typing import Optional


class OCRService:
    """Provide a consistent interface over different OCR providers."""

    def __init__(self, provider: str):
        self.provider = provider
        # TODO: initialize provider-specific SDK (Tesseract, Azure OCR, etc.).

    def extractTextFromImage(self, image_bytes: bytes, language: Optional[str] = None) -> str:
        """Extract plain text from images or scanned documents."""
        # TODO: support multi-page TIFFs and fallback strategies for low quality.
        raise NotImplementedError

    def extractTextFromPdf(self, pdf_bytes: bytes, language: Optional[str] = None) -> str:
        """Extract text from PDFs, optionally using hybrid OCR approaches."""
        # TODO: detect when native text exists vs. requiring OCR.
        raise NotImplementedError
