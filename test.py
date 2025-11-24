"""Backend smoke-test harness with optional DeepSeek passthrough.

Usage examples:

- Mocked DeepSeek (default): ``python test.py``
- Real DeepSeek with PDF ingestion: ``python test.py --mode real --pdf Documents/Documentos jurídicos/SJPI_281_2025.pdf``

The "real" mode extracts text from the provided PDF and calls the actual LLM
API, so remember to export ``DEEPSEEK_API_KEY`` (or set it in a .env file that
``backend.config`` reads.)
"""
from __future__ import annotations

import argparse
import json as jsonlib
import os
from contextlib import nullcontext
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, List
from unittest.mock import patch

import requests

from backend import config, schemas
from backend.clients.llm_client import LLMClient
from backend.services.classification_service import ClassificationService
from backend.services.legal_guide_service import LegalGuideService
from backend.services.safety_check_service import SafetyCheckService
from backend.services.simplification_service import SimplificationService


DEFAULT_PDF = Path("Documents/Documentos jurídicos/SJPI_281_2025.pdf")


class _MockResponse:
    """Simple stand-in for requests.Response."""

    def __init__(self, payload: Dict[str, Any], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self) -> Dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if not 200 <= self.status_code < 300:
            raise requests.HTTPError(f"Mock DeepSeek error {self.status_code}")


def _fake_deepseek_post(url: str, json: Dict[str, Any] | None = None, headers: Dict[str, str] | None = None, timeout: int = 60):
    """Return deterministic responses based on the DeepSeek system prompt."""

    payload = json or {}
    messages: List[Dict[str, str]] = payload.get("messages", [])
    system_prompt = messages[0]["content"] if messages else ""

    if "CLASIFICAR" in system_prompt:
        content = jsonlib.dumps(
            {
                "doc_type": "RESOLUCION_JURIDICA",
                "doc_subtype": "SENTENCIA",
                "confidence": 0.82,
            }
        )
    elif "Lenguaje Jurídico Claro" in system_prompt:
        content = "Este es un resumen claro y sencillo del texto legal original."
    elif "asistente jurídico" in system_prompt:
        content = jsonlib.dumps(
            {
                "meaning_for_you": "La sentencia confirma parcialmente su reclamación.",
                "what_to_do_now": "Revise los plazos para apelar si no está conforme.",
                "what_happens_next": "El juzgado notificará a las partes y se abrirá plazo de recursos.",
                "deadlines_and_risks": "Tiene 20 días hábiles para presentar recurso de apelación.",
            }
        )
    elif "revisor jurídico" in system_prompt:
        content = jsonlib.dumps({"is_safe": True, "warnings": []})
    else:
        raise RuntimeError("Mock DeepSeek handler no reconoce el prompt recibido.")

    response_payload = {"choices": [{"message": {"content": content}}]}
    return _MockResponse(response_payload)

def _load_pdf_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - handled via runtime error message
        raise RuntimeError(
            "pypdf is required for --mode real. Install it via 'pip install pypdf'."
        ) from exc

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found at {pdf_path}")

    reader = PdfReader(str(pdf_path))
    text_chunks: List[str] = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        text_chunks.append(extracted)

    text = "\n".join(text_chunks).strip()
    if not text:
        raise ValueError(f"No text could be extracted from {pdf_path}")
    return text


def _infer_sections(text: str) -> List[str]:
    keywords = [
        "ANTECEDENTES",
        "HECHOS",
        "FUNDAMENTOS",
        "FALLO",
        "RESUELVE",
    ]
    upper = text.upper()
    sections: List[str] = []
    for kw in keywords:
        if kw in upper:
            sections.append(kw.title())
    return sections


def _build_document(mode: str, pdf_path: Path) -> schemas.SegmentedDocument:
    if mode == "fake":
        return schemas.SegmentedDocument(
            normalizedText=(
                "SENTENCIA Nº 123/2023. La parte demandada dispone de 20 días hábiles para recurrir. "
                "Se condena al pago de 3.000 euros más intereses."
            ),
            sections=["Antecedentes de Hecho", "Fundamentos de Derecho", "Fallo"],
        )

    text = _load_pdf_text(pdf_path)
    return schemas.SegmentedDocument(
        normalizedText=text,
        sections=_infer_sections(text),
    )


def run_pipeline(mode: str, pdf_path: Path) -> Dict[str, Any]:
    if mode == "fake":
        os.environ.setdefault("DEEPSEEK_API_KEY", "sk-placeholder-demo-token")
    else:
        if not os.getenv("DEEPSEEK_API_KEY"):
            raise RuntimeError("Set DEEPSEEK_API_KEY before running in real mode.")

    cfg = config.load_config()
    settings = config.get_settings_dict(cfg)
    if not settings.get("llm_api_key"):
        settings["llm_api_key"] = os.getenv("DEEPSEEK_API_KEY") or "sk-placeholder-demo-token"
    client = LLMClient(settings)

    classifier = ClassificationService(client)
    simplifier = SimplificationService(client)
    guide_builder = LegalGuideService(client)
    safety = SafetyCheckService(client)

    document = _build_document(mode, pdf_path)
    patch_ctx = patch("requests.post", side_effect=_fake_deepseek_post) if mode == "fake" else nullcontext()

    with patch_ctx:
        classification = classifier.classifyWithLLM(document)
        simplification = simplifier.simplify(document, classification)
        guide = guide_builder.buildGuide(simplification)
        safety_rules = safety.ruleBasedCheck(document, simplification)
        safety_llm = safety.llmVerification(document, simplification, guide)

    return {
        "classification": classification.model_dump(),
        "simplification": simplification.model_dump(),
        "guide": guide.model_dump(),
        "rule_based_warnings": safety_rules.model_dump(),
        "llm_warnings": safety_llm.model_dump(),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backend DeepSeek service harness")
    parser.add_argument(
        "--mode",
        choices=["fake", "real"],
        default="fake",
        help="fake=mocked DeepSeek responses (no API key needed), real=call actual DeepSeek",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=DEFAULT_PDF,
        help="PDF path used when --mode real (default: SJPI_281_2025.pdf)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    mode_label = "mocked" if args.mode == "fake" else "real"
    print(f"Running backend service checks with {mode_label} DeepSeek mode...\n")
    results = run_pipeline(args.mode, args.pdf)
    pprint(results)


if __name__ == "__main__":
    main()
