"""Direct runner that instantiates DeepSeekLLMClient with env-provided key.

Use this when dependencies.get_llm_client does not pick up the env key.

Usage (PowerShell):
  $env:DEEPSEEK_API_KEY = '<key>'; python backend/scripts/run_llm_direct.py
"""
from __future__ import annotations

import json
import os
import sys
import traceback

# Ensure repo root is importable
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.clients import llm_client as _llm_mod
from backend.clients.llm_client import DeepSeekLLMClient
from backend import dependencies
from backend import schemas


PDF_PATH = r"C:\Users\Juan Sebastian Peña\Desktop\Accenture\GenAI-Mavericks-Challenge\Documents\Documentos jurídicos\SJPI_281_2025.pdf"


def extract_text_from_pdf(path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(path)
    parts = []
    for p in reader.pages:
        parts.append(p.extract_text() or "")
    return "\n\n".join(parts)


def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("LLM_API_KEY")
    if not api_key:
        print("ERROR: set DEEPSEEK_API_KEY or LLM_API_KEY in the environment.")
        sys.exit(2)

    settings = {
        "llm_api_key": api_key,
        "llm_base_url": os.environ.get("DEEPSEEK_BASE_URL") or None,
        # Enable tolerant parsing for noisy provider outputs (code fences, extra text)
        "tolerant_parse": True,
    }

    print(f"Using API key len={len(api_key)}")

    try:
        text = extract_text_from_pdf(PDF_PATH)
    except Exception as e:
        print("ERROR reading PDF:", e)
        traceback.print_exc()
        sys.exit(3)

    settings_obj = dependencies.get_settings()

    # Ensure the module placeholder constant won't accidentally match the real key
    # (some repos incorrectly set PLACEHOLDER_API_KEY to a test secret).
    try:
        _llm_mod.PLACEHOLDER_API_KEY = "__PLACEHOLDER__"
    except Exception:
        pass

    # Instantiate client directly with provided settings
    client = DeepSeekLLMClient(settings)

    # Manually instantiate dependencies the way FastAPI would resolve them.
    ocr_service = dependencies.get_ocr_service(settings=settings_obj)
    ingest_service = dependencies.get_ingest_service(settings=settings_obj, ocr_service=ocr_service)
    normalization_service = dependencies.get_normalization_service()
    classification_service = dependencies.get_classification_service(
        settings=settings_obj,
        llm_client_instance=client,
    )
    simplification_service = dependencies.get_simplification_service(llm_client_instance=client)
    legal_guide_service = dependencies.get_legal_guide_service(llm_client_instance=client)
    safety_check_service = dependencies.get_safety_check_service(llm_client_instance=client)

    import base64

    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    doc_input = schemas.DocumentInput(sourceType="pdf", fileContent=b64)

    try:
        ingest_result = ingest_service.ingest(doc_input)
        normalized = normalization_service.normalize(ingest_result)
        classification = classification_service.classify(normalized)
        simplification = simplification_service.simplify(normalized, classification)
        legal_guide = legal_guide_service.build_guide(normalized, classification, simplification)
        safety = safety_check_service.evaluate(normalized, simplification, legal_guide)
    except Exception as e:
        print("Pipeline execution failed:", e)
        traceback.print_exc()
        sys.exit(4)

    response = schemas.ProcessDocumentResponse(
        docType=classification.docType,
        docSubtype=classification.docSubtype,
        simplifiedText=simplification.simplifiedText,
        legalGuide=legal_guide,
        warnings=[issue.message for issue in safety.issues],
    )

    out = response.model_dump() if hasattr(response, "model_dump") else response.dict()
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
