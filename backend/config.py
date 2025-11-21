"""Configuration helpers for Justice Made Clear backend."""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Optional

import importlib

# Support both pydantic v1 and v2. Avoid attribute access that triggers
# pydantic's migration shim: check the package version instead.
_pydantic = importlib.import_module("pydantic")
_pyd_version = getattr(_pydantic, "__version__", "")
_pyd_major = _pyd_version.split(".")[0] if _pyd_version else None

if _pyd_major == "2":
    try:
        # pydantic v2 moved BaseSettings to the pydantic-settings package
        from pydantic_settings import BaseSettings  # type: ignore
        from pydantic import Field
    except Exception as exc:  # pragma: no cover - environment misconfiguration
        raise ImportError(
            "pydantic v2 detected but the `pydantic-settings` package is not installed. "
            "Install it with `pip install pydantic-settings` or pin pydantic to v1 (e.g. `pydantic==1.10.12`)."
        ) from exc
else:
    from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Environment-driven configuration used across the backend."""

    api_title: str = "Justice Made Clear API"
    api_version: str = "0.1.0"
    backend_cors_origins: str = "*"

    llm_provider: str = "deepseek"
    llm_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = Field(
        default=None, description="Fallback env var for backward compatibility."
    )
    llm_model_name: str = "deepseek-chat"
    llm_base_url: str = "https://api.deepseek.com"
    llm_request_timeout_seconds: int = 60
    llm_retries: int = 1
    llm_max_tokens: Optional[int] = None
    classification_temperature: float = 0.0
    simplification_temperature: float = 0.3
    guide_temperature: float = 0.25
    safety_temperature: float = 0.0
    classification_rule_threshold: float = 0.8
    classification_force_llm_threshold: float = 0.5

    ocr_provider: str = "tesseract"
    default_language: str = "es"
    pipeline_timeout_seconds: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def resolved_llm_api_key(self) -> Optional[str]:
        """Return whichever API key is available (llm_api_key preferred)."""
        return self.llm_api_key or self.deepseek_api_key


@lru_cache()
def get_settings() -> Settings:
    """Cached accessor used by FastAPI dependency injection."""
    return Settings()


# ---------------------------------------------------------------------------
# Backward compatibility helpers (legacy modules still import these names).
# ---------------------------------------------------------------------------

def load_config() -> Settings:
    """Alias maintained for legacy modules/tests."""
    return get_settings()


def get_settings_dict(settings: Settings | None = None) -> Dict[str, Any]:
    """Expose config as a plain dict for clients that prefer primitives."""
    settings = settings or get_settings()
    return {
        "llm_provider": settings.llm_provider,
        "llm_api_key": settings.resolved_llm_api_key,
        "llm_model_name": settings.llm_model_name,
        "llm_base_url": settings.llm_base_url,
        "llm_timeout": settings.llm_request_timeout_seconds,
        "llm_retries": settings.llm_retries,
        "llm_max_tokens": settings.llm_max_tokens,
        "classification_temperature": settings.classification_temperature,
        "simplification_temperature": settings.simplification_temperature,
        "guide_temperature": settings.guide_temperature,
        "safety_temperature": settings.safety_temperature,
        "classification_rule_threshold": settings.classification_rule_threshold,
        "classification_force_llm_threshold": settings.classification_force_llm_threshold,
        "ocr_provider": settings.ocr_provider,
        "default_language": settings.default_language,
        "pipeline_timeout_seconds": settings.pipeline_timeout_seconds,
        # Enable tolerant JSON parsing to handle fenced or decorated provider outputs.
        "tolerant_parse": True,
    }
