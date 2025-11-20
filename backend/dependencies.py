"""Dependency injection helpers for FastAPI routes."""
from __future__ import annotations

import logging

from fastapi import Depends

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

Settings = config.Settings
logger = logging.getLogger(__name__)


def get_settings() -> Settings:
    """Expose cached Settings instance for FastAPI."""
    return config.get_settings()


def get_llm_client(
    settings: Settings = Depends(get_settings),
) -> llm_client.BaseLLMClient:
    """Instantiate the configured LLM client implementation."""
    provider = settings.llm_provider.lower()
    llm_settings = config.get_settings_dict(settings)
    resolved_key = settings.resolved_llm_api_key

    if provider == "deepseek":
        if not resolved_key or resolved_key == llm_client.PLACEHOLDER_API_KEY:
            raise RuntimeError(
                "DeepSeek provider selected but no LLM_API_KEY/DEEPSEEK_API_KEY was provided. "
                "Set the environment variable before starting the backend."
            )
        return llm_client.DeepSeekLLMClient(settings=llm_settings)

    raise ValueError(
        f"Unsupported LLM provider '{settings.llm_provider}'. "
        "Set LLM_PROVIDER=deepseek (default) to use the DeepSeek integration."
    )


def get_ocr_service(
    settings: Settings = Depends(get_settings),
) -> ocr_client.OCRService:
    """Instantiate the OCR service wrapper."""
    return ocr_client.OCRService(provider=settings.ocr_provider)


def get_ingest_service(
    settings: Settings = Depends(get_settings),
    ocr_service: ocr_client.OCRService = Depends(get_ocr_service),
) -> ingest_service.IngestService:
    """Provide IngestService with OCR dependency."""
    return ingest_service.IngestService(
        ocr=ocr_service,
        default_language=settings.default_language,
    )


def get_normalization_service() -> normalization_service.NormalizationService:
    """Provide NormalizationService (stateless)."""
    return normalization_service.NormalizationService()


def get_classification_service(
    settings: Settings = Depends(get_settings),
    llm_client_instance: llm_client.BaseLLMClient = Depends(get_llm_client),
) -> classification_service.ClassificationService:
    """Provide ClassificationService with configured thresholds."""
    return classification_service.ClassificationService(
        client=llm_client_instance,
        rule_threshold=settings.classification_rule_threshold,
        force_llm_threshold=settings.classification_force_llm_threshold,
    )


def get_simplification_service(
    llm_client_instance: llm_client.BaseLLMClient = Depends(get_llm_client),
) -> simplification_service.SimplificationService:
    """Provide SimplificationService with the pluggable LLM."""
    return simplification_service.SimplificationService(client=llm_client_instance)


def get_legal_guide_service(
    llm_client_instance: llm_client.BaseLLMClient = Depends(get_llm_client),
) -> legal_guide_service.LegalGuideService:
    """Provide LegalGuideService."""
    return legal_guide_service.LegalGuideService(client=llm_client_instance)


def get_safety_check_service(
    llm_client_instance: llm_client.BaseLLMClient = Depends(get_llm_client),
) -> safety_check_service.SafetyCheckService:
    """Provide SafetyCheckService."""
    return safety_check_service.SafetyCheckService(client=llm_client_instance)
