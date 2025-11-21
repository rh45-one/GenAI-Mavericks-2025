from __future__ import annotations

import os
import pytest

from backend.clients.llm_client import DeepSeekLLMClient, LLMClientError


class MockResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def build_settings() -> dict:
    return {
        "llm_api_key": "test-key",
        "llm_base_url": "https://example.com",
        "llm_model_name": "deepseek-chat",
    }


def test_deepseek_classify_parses_payload(monkeypatch):
    payload = {
        "choices": [
            {
                "message": {
                    "content": '{"doc_type": "RESOLUCION_JURIDICA", "doc_subtype": "SENTENCIA", "confidence": 0.91, "rationale": "Coincide con Sentencia."}'
                }
            }
        ]
    }

    def fake_post(*args, **kwargs):
        return MockResponse(payload)

    monkeypatch.setattr("backend.clients.llm_client.requests.post", fake_post)

    client = DeepSeekLLMClient(settings=build_settings())
    result = client.classify("Sentencia con fallo.")

    assert result.docType == "RESOLUCION_JURIDICA"
    assert result.docSubtype == "SENTENCIA"
    assert result.source == "LLM"


def test_deepseek_generate_guide(monkeypatch):
    payload = {
        "choices": [
            {
                "message": {
                    "content": '{"meaning_for_you": "Resumen", "what_to_do_now": "Hacer", "what_happens_next": "Pasos", "deadlines_and_risks": "Riesgos"}'
                }
            }
        ]
    }

    def fake_post(*args, **kwargs):
        return MockResponse(payload)

    monkeypatch.setattr("backend.clients.llm_client.requests.post", fake_post)

    client = DeepSeekLLMClient(settings=build_settings())
    guide = client.generate_guide("Texto", context={"doc_type": "RESOLUCION_JURIDICA"})

    assert guide.meaningForYou == "Resumen"
    assert guide.provider == "deepseek"


def test_deepseek_invalid_json(monkeypatch):
    payload = {"choices": [{"message": {"content": "no-json"}}]}

    def fake_post(*args, **kwargs):
        return MockResponse(payload)

    monkeypatch.setattr("backend.clients.llm_client.requests.post", fake_post)
    client = DeepSeekLLMClient(settings=build_settings())

    with pytest.raises(LLMClientError):
        client.classify("texto")


@pytest.mark.real_llm
def test_deepseek_real_classification():
    api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("Requires LLM_API_KEY/DEEPSEEK_API_KEY")

    client = DeepSeekLLMClient(
        settings={
            "llm_api_key": api_key,
            "llm_base_url": os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
            "llm_model_name": os.getenv("LLM_MODEL_NAME", "deepseek-chat"),
        }
    )
    result = client.classify("SENTENCIA DEL JUZGADO DE 1ª INSTANCIA. FALLO: ...")
    assert result.docType in {"RESOLUCION_JURIDICA", "ESCRITO_PROCESAL", "OTRO"}
