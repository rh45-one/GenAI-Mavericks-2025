"""Unit test: pipeline smoke test using a FakeLLMClient (no network).

This test verifies services assemble correct DTOs when LLM returns
well-formed JSON. It keeps tests deterministic and fast.
"""
from __future__ import annotations

from backend.tests.mocks.fake_llm_client import FakeLLMClient
from backend.services.classification_service import ClassificationService
from backend.services.simplification_service import SimplificationService
from backend.services.legal_guide_service import LegalGuideService
from backend.services.safety_check_service import SafetyCheckService
from backend import schemas


def test_pipeline_with_fake_client():
    client = FakeLLMClient({})

    # classification thresholds: force LLM fallback for this test
    classification_service = ClassificationService(client, rule_threshold=0.99, force_llm_threshold=0.2)
    simplification_service = SimplificationService(client)
    legal_service = LegalGuideService(client)
    safety_service = SafetyCheckService(client)

    doc = schemas.SegmentedDocument(rawText="r", normalizedText="r", sections=[])

    classification = classification_service.classify(doc)
    assert classification.docType in {"RESOLUCION_JURIDICA", "ESCRITO_PROCESAL", "OTRO"}

    simplification = simplification_service.simplify(doc, classification)
    assert isinstance(simplification.simplifiedText, str) or isinstance(simplification, str)

    guide = legal_service.build_guide(doc, classification, simplification)
    assert hasattr(guide, "meaningForYou")

    safety = safety_service.evaluate(doc, simplification, guide)
    assert isinstance(safety.isSafe, bool)
