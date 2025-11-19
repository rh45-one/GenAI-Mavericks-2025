from __future__ import annotations

from backend import schemas
from backend.services.normalization_service import NormalizationService


def test_normalization_cleans_text():
    ingest_result = schemas.IngestResult(
        rawText="JUZGADO 5\r\n\r\n\r\nSENTENCIA -\n de prueba",
        metadata=schemas.DocumentMetadata(sourceType="text"),
    )
    service = NormalizationService()

    segmented = service.normalize(ingest_result)

    assert "JUZGADO" in segmented.normalizedText
    assert segmented.sections[0].name == "ENCABEZADO"
