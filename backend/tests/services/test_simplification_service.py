from __future__ import annotations

from backend import schemas
from backend.services.simplification_service import SimplificationService


def build_document(text: str) -> schemas.SegmentedDocument:
    return schemas.SegmentedDocument(
        rawText=text,
        normalizedText=text,
        sections=[schemas.DocumentSection(name="FALLO", content="contenido")],
    )


def test_simplification_strategy_resolution(fake_llm_client):
    service = SimplificationService(fake_llm_client)
    classification = schemas.ClassificationResult(
        docType="RESOLUCION_JURIDICA",
        docSubtype="SENTENCIA",
        confidence=0.9,
        source="RULES_ONLY",
        explanations=[],
    )

    result = service.simplify(build_document("texto"), classification)

    assert result.strategy == "resolution"
    assert result.provider == "fake"
    assert not result.truncated


def test_simplification_truncates_long_text(fake_llm_client):
    service = SimplificationService(fake_llm_client)
    classification = schemas.ClassificationResult(
        docType="RESOLUCION_JURIDICA",
        docSubtype="AUTO",
        confidence=0.9,
        source="RULES_ONLY",
        explanations=[],
    )
    long_text = "a" * 13000

    result = service.simplify(build_document(long_text), classification)

    assert result.truncated is True
    assert "trunc" in result.warnings[0]
