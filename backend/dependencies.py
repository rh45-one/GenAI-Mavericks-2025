"""Dependency injection helpers for FastAPI routes."""
from . import config
from .clients import llm_client, ocr_client


def get_config() -> config.AppConfig:
    """Provide application configuration to request handlers."""
    # TODO: cache loaded config to avoid re-reading environment per request.
    return config.load_config()


def get_llm_client(app_config: config.AppConfig = None) -> llm_client.LLMClient:
    """Instantiate the LLM client wrapper."""
    if app_config is None:
        app_config = get_config()
    # TODO: share a single client instance across requests if desired.
    return llm_client.LLMClient(settings=config.get_settings_dict(app_config))


def get_ocr_service(app_config: config.AppConfig = None) -> ocr_client.OCRService:
    """Instantiate the OCR service wrapper."""
    if app_config is None:
        app_config = get_config()
    # TODO: configure OCR providers (on-prem Tesseract vs. managed API).
    return ocr_client.OCRService(provider=app_config.ocr_provider)
