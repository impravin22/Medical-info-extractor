from __future__ import annotations

from typing import Optional, Annotated

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore[reportMissingImports]


class Settings(BaseSettings):
    # Select LLM provider: "gemini" or "hf"
    llm_backend: Annotated[
        str,
        Field(
            default="gemini",
            validation_alias=AliasChoices(
                "MSB_LLM_BACKEND", "LLM_BACKEND", "llm_backend"
            ),
        ),
    ]

    # Model configuration for Transformers
    llm_model: Annotated[
        str,
        Field(
            default="Qwen/Qwen2.5-7B-Instruct",
            validation_alias=AliasChoices("MSB_LLM_MODEL", "LLM_MODEL", "llm_model"),
        ),
    ]
    # Keep gemini_model for backward compatibility with CLI args
    gemini_model: Annotated[
        str,
        Field(
            default="gemini-1.5-flash",
            validation_alias=AliasChoices(
                "MSB_GEMINI_MODEL", "GOOGLE_AI_DEFAULT_MODEL", "google_ai_default_model"
            ),
        ),
    ]

    # Gemini API key
    gemini_api_key: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices(
                "MSB_GEMINI_API_KEY", "GOOGLE_API_KEY", "google_api_key"
            ),
        ),
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
