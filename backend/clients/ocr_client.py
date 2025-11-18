"""OCR client wrapper for Justice Made Clear."""
from __future__ import annotations

from typing import Optional
import io

# Intentamos usar pypdf o, si no está, PyPDF2 como fallback
try:
    import pypdf
except ImportError:  # pragma: no cover
    try:
        import PyPDF2 as pypdf  # type: ignore
    except ImportError:
        pypdf = None  # type: ignore


class OCRService:
    """
    Provide a consistent interface over different OCR providers.

    En esta versión:
    - Para PDF usamos extracción de texto con pypdf / PyPDF2 (no OCR "real", pero suficiente
      para sentencias típicas que ya traen texto).
    - Para imágenes, intentamos usar pytesseract si está instalado; si no, levantamos
      un error claro explicando qué falta.
    """

    def __init__(self, provider: str = "pypdf"):
        # provider queda por si más adelante añadimos otros backends (Azure, etc.)
        self.provider = provider

    # ------------------------------------------------------------------
    # PDF → TEXTO
    # ------------------------------------------------------------------
    def extractTextFromPdf(self, pdf_bytes: bytes, language: Optional[str] = None) -> str:
        """
        Extract text from PDFs.

        Estrategia:
        - Usar pypdf / PyPDF2 para extraer el texto embebido.
        - Concatenar todas las páginas.
        - Si pypdf no está instalado, lanzar un error con instrucción de instalación.
        """
        if pypdf is None:
            raise RuntimeError(
                "pypdf / PyPDF2 no está instalado. Instala con: pip install pypdf"
            )

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pages_text: list[str] = []

        for page in reader.pages:
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            pages_text.append(page_text)

        full_text = "\n\n".join(pages_text).strip()
        return full_text

    # ------------------------------------------------------------------
    # IMAGEN → TEXTO (opcional)
    # ------------------------------------------------------------------
    def extractTextFromImage(self, image_bytes: bytes, language: Optional[str] = None) -> str:
        """
        Extract plain text from images or scanned documents.

        - Intenta usar pytesseract + Pillow (PIL).
        - Si no están instalados, lanza un error claro con instrucciones.
        """
        try:
            from PIL import Image
            import pytesseract
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "OCR de imágenes requiere 'pytesseract' y 'Pillow'. "
                "Instala con: pip install pytesseract pillow"
            ) from e

        img = Image.open(io.BytesIO(image_bytes))

        config = ""
        if language:
            # pytesseract usa -l para el idioma (ej: 'spa' para español)
            config = f"-l {language}"

        text = pytesseract.image_to_string(img, config=config)
        return text
