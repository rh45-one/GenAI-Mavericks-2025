"""Configuration helpers for Justice Made Clear backend."""
from typing import Any, Dict


class AppConfig:
    """Placeholder settings object shared across modules."""

    # TODO: load from environment or configuration files.
    llm_api_key: str | None = None
    llm_model_name: str = "gpt-placeholder"
    ocr_provider: str = "tesseract"
    default_language: str = "es"
    pipeline_timeout_seconds: int = 60
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1500


def load_config() -> "AppConfig":
    """Assemble AppConfig from environment variables or .env files."""
    # TODO: integrate python-dotenv + os.environ lookups.
    # TODO: validate required values such as API keys.
    return AppConfig()


def get_settings_dict(config: "AppConfig") -> Dict[str, Any]:
    """Expose config as a plain dict for clients that prefer primitives."""
    return {
        "llm_api_key": config.llm_api_key,
        "llm_model_name": config.llm_model_name,
        "ocr_provider": config.ocr_provider,
        "default_language": config.default_language,
        "pipeline_timeout_seconds": config.pipeline_timeout_seconds,
        "llm_temperature": config.llm_temperature,
        "llm_max_tokens": config.llm_max_tokens,
    }
