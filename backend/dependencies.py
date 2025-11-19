"""Dependency injection helpers for FastAPI routes."""
from __future__ import annotations

from functools import lru_cache

from . import config
from .clients import llm_client, ocr_client
from .services import (
    classification_service,
    ingest_service,
    legal_guide_service,
    normalization_service,
    safety_check_service,
    simplification_service,
)


@lru_cache()
def get_config() -> config.AppConfig:
    """Provide cached application configuration."""
    return config.load_config()


def get_llm_client(app_config: config.AppConfig | None = None) -> llm_client.BaseLLMClient:
    """Instantiate the pluggable LLM client."""
    if app_config is None:
        app_config = get_config()

    settings = config.get_settings_dict(app_config)
    provider = app_config.llm_provider

    if provider == "deepseek":
        return llm_client.DeepSeekLLMClient(settings=settings)

    raise ValueError(f"Unsupported LLM provider '{provider}'.")


def get_ocr_service(app_config: config.AppConfig | None = None) -> ocr_client.OCRService:
    """Instantiate the OCR service wrapper."""
    if app_config is None:
        app_config = get_config()
    return ocr_client.OCRService(provider=app_config.ocr_provider)


def get_ingest_service(
    ocr_service: ocr_client.OCRService | None = None,
    app_config: config.AppConfig | None = None,
) -> ingest_service.IngestService:
    """Provide IngestService with its OCR dependency."""
    if ocr_service is None:
        ocr_service = get_ocr_service(app_config)
    if app_config is None:
        app_config = get_config()
    return ingest_service.IngestService(ocr=ocr_service, default_language=app_config.default_language)


def get_normalization_service() -> normalization_service.NormalizationService:
    """Provide NormalizationService (stateless)."""
    return normalization_service.NormalizationService()


def get_classification_service(
    llm_client_instance: llm_client.BaseLLMClient | None = None,
    app_config: config.AppConfig | None = None,
) -> classification_service.ClassificationService:
    """Provide ClassificationService with thresholds from config."""
    if app_config is None:
        app_config = get_config()
    if llm_client_instance is None:
        llm_client_instance = get_llm_client(app_config)
    return classification_service.ClassificationService(
        client=llm_client_instance,
        rule_threshold=app_config.classification_rule_threshold,
        force_llm_threshold=app_config.classification_force_llm_threshold,
    )


def get_simplification_service(
    llm_client_instance: llm_client.BaseLLMClient | None = None,
) -> simplification_service.SimplificationService:
    """Provide SimplificationService with the configured LLM."""
    if llm_client_instance is None:
        llm_client_instance = get_llm_client()
    return simplification_service.SimplificationService(client=llm_client_instance)


def get_legal_guide_service(
    llm_client_instance: llm_client.BaseLLMClient | None = None,
) -> legal_guide_service.LegalGuideService:
    """Provide LegalGuideService."""
    if llm_client_instance is None:
        llm_client_instance = get_llm_client()
    return legal_guide_service.LegalGuideService(client=llm_client_instance)


def get_safety_check_service(
    llm_client_instance: llm_client.BaseLLMClient | None = None,
) -> safety_check_service.SafetyCheckService:
    """Provide SafetyCheckService."""
    if llm_client_instance is None:
        llm_client_instance = get_llm_client()
    return safety_check_service.SafetyCheckService(client=llm_client_instance)
