"""Configuration helpers for Justice Made Clear backend."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AppConfig:
    """Container for backend settings and pipeline knobs."""

    llm_provider: str
    llm_api_key: Optional[str]
    llm_model_name: str
    llm_base_url: str
    llm_request_timeout_seconds: int
    llm_retries: int
    llm_max_tokens: Optional[int]
    classification_temperature: float
    simplification_temperature: float
    guide_temperature: float
    safety_temperature: float
    classification_rule_threshold: float
    classification_force_llm_threshold: float
    ocr_provider: str
    default_language: str
    pipeline_timeout_seconds: int


def _get_env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value not in (None, "") else default


def _get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value not in (None, "") else default


def _get_env_optional_int(name: str) -> Optional[int]:
    value = os.getenv(name)
    return int(value) if value not in (None, "") else None


def load_config() -> AppConfig:
    """Assemble AppConfig from environment variables or .env files."""

    llm_provider = os.getenv("LLM_PROVIDER", "deepseek").lower()
    default_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    default_base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    if llm_provider == "openai":
        default_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        default_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    return AppConfig(
        llm_provider=llm_provider,
        llm_api_key=os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY"),
        llm_model_name=os.getenv("LLM_MODEL_NAME", default_model),
        llm_base_url=os.getenv("LLM_BASE_URL", default_base_url),
        llm_request_timeout_seconds=_get_env_int("LLM_TIMEOUT_SECONDS", 60),
        llm_retries=_get_env_int("LLM_RETRIES", 1),
        llm_max_tokens=_get_env_optional_int("LLM_MAX_TOKENS"),
        classification_temperature=_get_env_float("LLM_CLASSIFICATION_TEMPERATURE", 0.0),
        simplification_temperature=_get_env_float("LLM_SIMPLIFICATION_TEMPERATURE", 0.3),
        guide_temperature=_get_env_float("LLM_GUIDE_TEMPERATURE", 0.25),
        safety_temperature=_get_env_float("LLM_SAFETY_TEMPERATURE", 0.0),
        classification_rule_threshold=_get_env_float("CLASSIFICATION_RULE_THRESHOLD", 0.8),
        classification_force_llm_threshold=_get_env_float(
            "CLASSIFICATION_FORCE_LLM_THRESHOLD", 0.5
        ),
        ocr_provider=os.getenv("OCR_PROVIDER", "tesseract"),
        default_language=os.getenv("DEFAULT_LANGUAGE", "es"),
        pipeline_timeout_seconds=_get_env_int("PIPELINE_TIMEOUT_SECONDS", 60),
    )


def get_settings_dict(config: AppConfig) -> Dict[str, Any]:
    """Expose config as a plain dict for clients that prefer primitives."""

    return {
        "llm_provider": config.llm_provider,
        "llm_api_key": config.llm_api_key,
        "llm_model_name": config.llm_model_name,
        "llm_base_url": config.llm_base_url,
        "llm_timeout": config.llm_request_timeout_seconds,
        "llm_retries": config.llm_retries,
        "llm_max_tokens": config.llm_max_tokens,
        "classification_temperature": config.classification_temperature,
        "simplification_temperature": config.simplification_temperature,
        "guide_temperature": config.guide_temperature,
        "safety_temperature": config.safety_temperature,
        "classification_rule_threshold": config.classification_rule_threshold,
        "classification_force_llm_threshold": config.classification_force_llm_threshold,
        "ocr_provider": config.ocr_provider,
        "default_language": config.default_language,
        "pipeline_timeout_seconds": config.pipeline_timeout_seconds,
    }
