from __future__ import annotations

from backend.services.legal_guide_service import LegalGuideService


def test_legal_guide_service_delegates(fake_llm_client, sample_segmented_document, sample_classification_result, sample_simplification_result):
    service = LegalGuideService(fake_llm_client)
    guide = service.build_guide(sample_segmented_document, sample_classification_result, sample_simplification_result)

    assert guide.meaningForYou == "Resumen"
    assert guide.provider == "fake"
