from __future__ import annotations

import sys
import types

from backend.clients import ocr_client


class FakePage:
    def __init__(self, text: str):
        self._text = text

    def extract_text(self):
        return self._text


class FakePdfReader:
    def __init__(self, *_args, **_kwargs):
        self.pages = [FakePage("Primera pagina"), FakePage("Segunda pagina")]


def test_extract_text_from_pdf(monkeypatch):
    monkeypatch.setattr(ocr_client, "pypdf", types.SimpleNamespace(PdfReader=FakePdfReader))

    service = ocr_client.OCRService()
    text = service.extract_text_from_pdf(b"pdf-bytes")
    assert "Primera" in text and "Segunda" in text


def test_extract_text_from_image(monkeypatch):
    fake_pil = types.ModuleType("PIL")
    fake_image_module = types.ModuleType("Image")

    def fake_open(_bytes):
        return "image"

    fake_image_module.open = fake_open  # type: ignore[attr-defined]
    fake_pil.Image = fake_image_module  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "PIL", fake_pil)
    monkeypatch.setitem(sys.modules, "PIL.Image", fake_image_module)
    monkeypatch.setitem(
        sys.modules,
        "pytesseract",
        types.SimpleNamespace(image_to_string=lambda *args, **kwargs: "texto ocr"),
    )

    service = ocr_client.OCRService()
    text = service.extract_text_from_image(b"image-bytes")
    assert text == "texto ocr"
