from __future__ import annotations

from backend import schemas
from backend.services.classification_service import ClassificationService


def test_classification_rules_confident(fake_llm_client):
    document = schemas.SegmentedDocument(
        rawText="SENTENCIA con fallo",
        normalizedText="SENTENCIA con fallo",
        sections=[schemas.DocumentSection(name="FALLO", content="...")],
    )

    service = ClassificationService(fake_llm_client, rule_threshold=0.8, force_llm_threshold=0.4)
    result = service.classify(document)

    assert result.docType == "RESOLUCION_JURIDICA"
    assert result.source == "RULES_ONLY"


def test_classification_llm_fallback(fake_llm_client):
    document = schemas.SegmentedDocument(
        rawText="Documento sin palabras clave",
        normalizedText="Documento sin palabras clave",
        sections=[],
    )
    fake_llm_client.classification_result = schemas.ClassificationResult(
        docType="ESCRITO_PROCESAL",
        docSubtype="DEMANDA",
        confidence=0.7,
        source="LLM",
        explanations=["LLM"],
    )

    service = ClassificationService(fake_llm_client, rule_threshold=0.8, force_llm_threshold=0.5)
    result = service.classify(document)

    assert result.docType == "ESCRITO_PROCESAL"
    assert result.source == "HYBRID"
