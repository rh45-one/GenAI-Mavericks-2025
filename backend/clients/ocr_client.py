"""OCR client wrapper for Justice Made Clear."""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional

# Attempt to use pypdf, fall back to PyPDF2 when necessary.
try:
    import pypdf
except ImportError:  # pragma: no cover
    try:
        import PyPDF2 as pypdf  # type: ignore
    except ImportError:  # pragma: no cover
        pypdf = None  # type: ignore


class OCRClientError(RuntimeError):
    """Raised when the OCR provider cannot process the file."""


@dataclass
class OCRService:
    """Provide a consistent interface over different OCR providers."""

    provider: str = "pypdf"

    # ------------------------------------------------------------------
    # PDF -> TEXT
    # ------------------------------------------------------------------
    def extract_text_from_pdf(self, pdf_bytes: bytes, language: Optional[str] = None) -> str:
        """Extract text from PDFs using embedded content when available."""
        if pypdf is None:
            raise OCRClientError(
                "pypdf / PyPDF2 is required for PDF extraction. Install with: pip install pypdf"
            )

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pages_text: list[str] = []

        for page in reader.pages:
            try:
                page_text = page.extract_text() or ""
            except Exception as exc:  # pragma: no cover - backend specific
                raise OCRClientError(f"Failed to extract text from PDF page: {exc}") from exc
            pages_text.append(page_text)

        return "\n\n".join(pages_text).strip()

    # ------------------------------------------------------------------
    # IMAGE -> TEXT
    # ------------------------------------------------------------------
    def extract_text_from_image(self, image_bytes: bytes, language: Optional[str] = None) -> str:
        """Extract plain text from images or scanned documents via pytesseract."""
        try:
            from PIL import Image
            import pytesseract
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise OCRClientError(
                "Image OCR requires 'pytesseract' and 'Pillow'. Install with: pip install pytesseract pillow"
            ) from exc

        image = Image.open(io.BytesIO(image_bytes))
        config = f"-l {language}" if language else ""
        return pytesseract.image_to_string(image, config=config)
