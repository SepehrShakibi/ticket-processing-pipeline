import os
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field, SecretStr, field_validator

from src.config import Config

class APISettings(BaseModel):
    """Validated runtime settings for the API"""

    provider: Literal["openai"] = "openai"
    api_key: SecretStr
    model_name: str = Field(min_length=1)
    base_url: AnyHttpUrl | None = None
    model_timeout_seconds: float = Field(default=30.0, gt=0.0, le=120.0)
    output_retries: int = Field(default=1, ge=0, le=2)

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("OPEN_API_KEY must be configured.")

        return value

    @classmethod
    def from_environment(cls) -> "APISettings":
        """"Load settings using the projects's existing environment setup."""
        return cls.model_validate(
            {
                "provider": os.getenv("LLM_PROVIDER","openai").strip().lower(),
                "api_key": (Config.OPENAI_API_KEY or "").strip(),
                "model_name": (Config.OPENAI_MODEL_NAME or "").strip(),
                "base_url": (Config.OPENAI_BASE_URL or "").strip() or None,
                "model_timeout_seconds": os.getenv("API_MODEL_TIMEPIT_SECONDS","30"),
                "output_retries": os.getenv("API_OUTPUT_RETRIES", "1"),

            }
        )
