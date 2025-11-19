from __future__ import annotations

from backend import schemas
from backend.services.safety_check_service import SafetyCheckService


def make_segmented(text: str) -> schemas.SegmentedDocument:
    return schemas.SegmentedDocument(
        rawText=text,
        normalizedText=text,
        sections=[],
    )


def test_safety_flags_detect_missing_amounts(fake_llm_client, sample_simplification_result):
    service = SafetyCheckService(fake_llm_client)
    original = make_segmented("Se impone multa de $5.000 COP. Fecha limite 10/05/2024.")
    simplified = sample_simplification_result.model_copy(
        update={"simplifiedText": "Resumen sin datos"}
    )
    fake_llm_client.safety_payload = {"is_safe": False, "warnings": ["Falta informacion"], "verdict": "riesgo"}

    result = service.evaluate(original, simplified, fake_llm_client.guide)

    assert any(issue.code.startswith("MISSING_AMOUNT") for issue in result.issues)
    assert result.llmVerdict == "riesgo"
    assert result.isSafe is False
