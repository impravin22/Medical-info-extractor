from __future__ import annotations

from typing import Optional, Annotated

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore[reportMissingImports]


class Settings(BaseSettings):
    # Select LLM provider: "gemini", "nebius", or "hf"
    llm_backend: Annotated[
        str,
        Field(
            default="nebius",
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

    # Nebius API configuration
    nebius_api_key: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices(
                "MSB_NEBIUS_API_KEY", "NEBIUS_API_KEY", "nebius_api_key"
            ),
        ),
    ]
    nebius_model: Annotated[
        str,
        Field(
            default="NousResearch/Hermes-4-405B",
            validation_alias=AliasChoices(
                "MSB_NEBIUS_MODEL", "NEBIUS_MODEL", "nebius_model"
            ),
        ),
    ]
    nebius_base_url: Annotated[
        str,
        Field(
            default="https://api.studio.nebius.ai/v1/",
            validation_alias=AliasChoices(
                "MSB_NEBIUS_BASE_URL", "NEBIUS_BASE_URL", "nebius_base_url"
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
