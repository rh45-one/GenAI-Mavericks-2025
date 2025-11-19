from __future__ import annotations

import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:  # pragma: no cover - test bootstrap
    sys.path.insert(0, str(ROOT))

from backend import schemas
from backend.clients.llm_client import BaseLLMClient
from backend.clients.ocr_client import OCRService


class FakeLLMClient(BaseLLMClient):
    """Deterministic stand-in for the pluggable LLM client."""

    def __init__(self):
        super().__init__({})
        self.classification_result = schemas.ClassificationResult(
            docType="OTRO",
            docSubtype="DESCONOCIDO",
            confidence=0.2,
            source="FAKE",
            explanations=["fake"],
        )
        self.simplified_text = "Texto simplificado."
        self.guide = schemas.LegalGuide(
            meaningForYou="Resumen",
            whatToDoNow="Acciones",
            whatHappensNext="Pasos",
            deadlinesAndRisks="Plazos",
            provider="fake",
        )
        self.safety_payload = {"is_safe": True, "warnings": [], "verdict": "ok"}

    @property
    def provider_name(self) -> str:  # pragma: no cover - trivial property
        return "fake"

    def classify(self, text: str, sections=None) -> schemas.ClassificationResult:
        return self.classification_result

    def simplify(self, text: str, doc_type: str, doc_subtype: str) -> str:
        return self.simplified_text

    def generate_guide(self, simplified_text: str, context):
        return self.guide

    def verify_safety(self, original_text: str, simplified_text: str, legal_guide: schemas.LegalGuide):
        return self.safety_payload


class FakeOCRService(OCRService):
    """Fake OCR returning canned values without touching pypdf/pytesseract."""

    def __init__(self, pdf_text: str = "PDF TEXT", image_text: str = "IMAGE TEXT"):
        super().__init__(provider="fake")
        self.pdf_text = pdf_text
        self.image_text = image_text

    def extract_text_from_pdf(self, pdf_bytes: bytes, language=None) -> str:
        return self.pdf_text

    def extract_text_from_image(self, image_bytes: bytes, language=None) -> str:
        return self.image_text


@pytest.fixture
def fake_llm_client() -> FakeLLMClient:
    return FakeLLMClient()


@pytest.fixture
def fake_ocr_service() -> FakeOCRService:
    return FakeOCRService()


@pytest.fixture
def sample_segmented_document() -> schemas.SegmentedDocument:
    return schemas.SegmentedDocument(
        rawText="Encabezado\nFallo",
        normalizedText="Encabezado\n\nFallo",
        sections=[
            schemas.DocumentSection(name="ENCABEZADO", content="Encabezado..."),
            schemas.DocumentSection(name="FALLO", content="Fallo..."),
        ],
    )


@pytest.fixture
def sample_classification_result() -> schemas.ClassificationResult:
    return schemas.ClassificationResult(
        docType="RESOLUCION_JURIDICA",
        docSubtype="SENTENCIA",
        confidence=0.9,
        source="RULES_ONLY",
        explanations=["Reglas"],
    )


@pytest.fixture
def sample_simplification_result(sample_classification_result) -> schemas.SimplificationResult:
    return schemas.SimplificationResult(
        simplifiedText="Texto simplificado.",
        docType=sample_classification_result.docType,
        docSubtype=sample_classification_result.docSubtype,
        importantSections=[
            schemas.DocumentSection(name="FALLO", content="..."),
        ],
        strategy="resolution",
        provider="fake",
        truncated=False,
        warnings=[],
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "real_llm: marks tests that hit a real LLM API (opt-in via USE_REAL_LLM)."
    )


def pytest_collection_modifyitems(config, items):
    if os.getenv("USE_REAL_LLM"):
        return

    skip_marker = pytest.mark.skip(reason="Set USE_REAL_LLM=true to run this test.")
    for item in items:
        if "real_llm" in item.keywords:
            item.add_marker(skip_marker)
