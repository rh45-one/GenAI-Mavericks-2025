"""Small runner to test backend/clients/llm_client.py against a local PDF and the DeepSeek API.

Usage (PowerShell):
  setx DEEPSEEK_API_KEY "<your_key>"   # or set in the current session: $env:DEEPSEEK_API_KEY = '<your_key>'
  python backend\scripts\test_llm_run.py

The script reads the PDF at the path configured below, extracts text with pypdf,
creates an LLMClient with the API key from env var `DEEPSEEK_API_KEY` and calls
`callClassifier` on the first snippet of text. Results printed as JSON.
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Any

# Ensure repo root is importable when running this script directly
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Import the module early so we can temporarily disable the placeholder-key
# rejection (only for this local test runner). This avoids editing library code.
try:
    import importlib
    llm_mod = importlib.import_module("backend.clients.llm_client")
    # Disable placeholder equality check by setting the sentinel to a unique value
    # This lets us use the provided key even if it equals the module's placeholder.
    setattr(llm_mod, "PLACEHOLDER_API_KEY", "__TEST_DISABLED_PLACEHOLDER__")
except Exception:
    # If the module cannot be imported yet, we'll handle it later when importing the class.
    llm_mod = None

# Path to the PDF to test
PDF_PATH = r"C:\Users\Juan Sebastian Peña\Desktop\Accenture\GenAI-Mavericks-Challenge\Documents\Documentos jurídicos\SJPI_281_2025.pdf"

# Maximum characters to send to classifier (keep below provider limits)
SNIPPET_MAX = 8000

try:
    # Support the concrete class name used in the repo (DeepSeekLLMClient)
    from backend.clients.llm_client import DeepSeekLLMClient as LLMClient
except Exception:
    try:
        from backend.clients.llm_client import LLMClient  # backward compatibility
    except Exception as e:
        print("ERROR: Could not import LLMClient or DeepSeekLLMClient:", e)
        traceback.print_exc()
        sys.exit(2)

# Provide a tolerant JSON extractor to handle code fences or surrounding markdown
def tolerant_parse(payload: str) -> dict:
    """Try to extract JSON object from payload that may include markdown fences.

    Strategies:
    - Remove triple backticks and leading 'json' markers.
    - Find first '{' and last '}' and attempt to parse that substring.
    """
    if not isinstance(payload, str):
        raise ValueError("Payload is not a string")

    p = payload.strip()
    # Remove code fences ```json ... ``` or ``` ... ```
    if p.startswith("```"):
        # remove leading fence
        p = p.lstrip("`")
        # sometimes the fence includes a language marker like 'json'
        if p.lower().startswith("json"):
            p = p[4:]
        p = p.strip()
        # remove trailing fences
        if p.endswith("```"):
            p = p[:-3].strip()

    # locate first JSON object
    first = p.find("{")
    last = p.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidate = p[first : last + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Fall back to direct parse
    return json.loads(p)

# Monkeypatch the class parse function to be tolerant for this test run only.
try:
    import backend.clients.llm_client as _mod
    if hasattr(_mod, "DeepSeekLLMClient"):
        _mod.DeepSeekLLMClient._parse_json = staticmethod(tolerant_parse)
    if hasattr(_mod, "LLMClient"):
        _mod.LLMClient._parse_json = staticmethod(tolerant_parse)
except Exception:
    pass

try:
    from pypdf import PdfReader
except Exception as e:
    print("ERROR: pypdf not available:", e)
    traceback.print_exc()
    sys.exit(2)


def extract_text_from_pdf(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF not found: {path}")
    reader = PdfReader(path)
    parts = []
    for p in reader.pages:
        try:
            txt = p.extract_text() or ""
        except Exception:
            txt = ""
        parts.append(txt)
    return "\n\n".join(parts)


def main() -> None:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("ERROR: environment variable DEEPSEEK_API_KEY is not set.")
        print("Set it in PowerShell with: $env:DEEPSEEK_API_KEY = '<your_key>'")
        sys.exit(3)

    settings = {
        "llm_api_key": api_key,
        # Optional: override base url with DEEPSEEK_BASE_URL env var
        "llm_base_url": os.environ.get("DEEPSEEK_BASE_URL") or None,
    }

    # Debug: show the key length to detect accidental whitespace/newlines
    print(f"DEEPSEEK_API_KEY repr: {repr(api_key)} (len={len(api_key) if api_key else 0})")

    print("Reading PDF (this may take a few seconds)...")
    try:
        text = extract_text_from_pdf(PDF_PATH)
    except Exception as e:
        print("Failed to read PDF:", e)
        traceback.print_exc()
        sys.exit(4)

    snippet = text[:SNIPPET_MAX]
    print(f"Extracted {len(text)} characters; using snippet of {len(snippet)} chars for classification.")

    # Instantiate configured services via dependency helpers for parity with the app
    try:
        from backend import dependencies
        from backend import schemas
    except Exception as e:
        print("ERROR: Could not import dependencies/schemas:", e)
        traceback.print_exc()
        sys.exit(6)

    app_config = dependencies.get_config()

    # Build LLM client using the app config (this will pick DEEPSEEK provider)
    llm_client_instance = dependencies.get_llm_client(app_config)
    ocr_service = dependencies.get_ocr_service(app_config)

    ingest_service = dependencies.get_ingest_service(ocr_service, app_config)
    normalization_service = dependencies.get_normalization_service()
    classification_service = dependencies.get_classification_service(llm_client_instance, app_config)
    simplification_service = dependencies.get_simplification_service(llm_client_instance)
    legal_guide_service = dependencies.get_legal_guide_service(llm_client_instance)
    safety_check_service = dependencies.get_safety_check_service(llm_client_instance)

    # Prepare DocumentInput with base64 file content
    import base64

    try:
        with open(PDF_PATH, "rb") as f:
            pdf_bytes = f.read()
    except Exception as e:
        print("ERROR: Could not read PDF file:", e)
        traceback.print_exc()
        sys.exit(7)

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
        sys.exit(8)

    # Assemble final ProcessDocumentResponse
    response = schemas.ProcessDocumentResponse(
        docType=classification.docType,
        docSubtype=classification.docSubtype,
        simplifiedText=simplification.simplifiedText,
        legalGuide=legal_guide,
        warnings=[issue.message for issue in safety.issues],
    )

    # Print full JSON output
    out = response.model_dump() if hasattr(response, "model_dump") else response.dict()
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
