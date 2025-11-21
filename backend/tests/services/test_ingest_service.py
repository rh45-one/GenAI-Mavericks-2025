from __future__ import annotations

import base64
import pytest

from backend import schemas
from backend.services.ingest_service import IngestService


def test_ingest_text_returns_metadata(fake_ocr_service):
    service = IngestService(fake_ocr_service, default_language="es")
    document_input = schemas.DocumentInput(sourceType="text", plainText=" Hola ")

    result = service.ingest(document_input)

    assert result.rawText == "Hola"
    assert result.metadata.sourceType == "text"
    assert result.metadata.charLength == 4


def test_ingest_pdf_uses_ocr(fake_ocr_service):
    service = IngestService(fake_ocr_service, default_language="es")
    pdf_bytes = base64.b64encode(b"pdf-file").decode("utf-8")
    document_input = schemas.DocumentInput(sourceType="pdf", fileContent=pdf_bytes)

    result = service.ingest(document_input)

    assert result.rawText == fake_ocr_service.pdf_text
    assert result.metadata.sourceType == "pdf"


def test_ingest_invalid_source(fake_ocr_service):
    service = IngestService(fake_ocr_service)
    with pytest.raises(ValueError):
        service.ingest(schemas.DocumentInput(sourceType="unknown"))
