"""Configuration helpers for Justice Made Clear backend."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AppConfig:
    """Simple container for backend settings."""

    llm_api_key: str | None
    llm_model_name: str
    llm_base_url: str
    ocr_provider: str
    default_language: str
    pipeline_timeout_seconds: int
    llm_temperature: float
    llm_max_tokens: int


def load_config() -> AppConfig:
    """Assemble AppConfig from environment variables or .env files."""
    return AppConfig(
        llm_api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY"),
        llm_model_name=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        llm_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        ocr_provider=os.getenv("OCR_PROVIDER", "tesseract"),
        default_language=os.getenv("DEFAULT_LANGUAGE", "es"),
        pipeline_timeout_seconds=int(os.getenv("PIPELINE_TIMEOUT_SECONDS", "60")),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1500")),
    )


def get_settings_dict(config: AppConfig) -> Dict[str, Any]:
    """Expose config as a plain dict for clients that prefer primitives."""
    return {
        "llm_api_key": config.llm_api_key,
        "llm_model_name": config.llm_model_name,
        "llm_base_url": config.llm_base_url,
        "ocr_provider": config.ocr_provider,
        "default_language": config.default_language,
        "pipeline_timeout_seconds": config.pipeline_timeout_seconds,
        "llm_temperature": config.llm_temperature,
        "llm_max_tokens": config.llm_max_tokens,
    }
