"""Application configuration with environment-variable overrides."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProvider(StrEnum):
    """Chat completion backend — see ``oh_agent.agents.llm_client``."""

    LITELLM = "litellm"
    OPENROUTER = "openrouter"
    OPENAI = "openai"


class Settings(BaseSettings):
    """Central configuration loaded from environment variables (prefix ``OH_``)."""

    model_config = {"env_prefix": "OH_", "env_file": ".env", "extra": "ignore"}

    # --- General ---
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # --- API ---
    api_host: str = "0.0.0.0"  # noqa: S104
    api_port: int = 8000
    api_title: str = "OH AI Agent"
    api_version: str = "0.1.0"
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])

    # --- LLM ---
    llm_provider: LLMProvider = Field(
        default=LLMProvider.LITELLM,
        description=(
            "Completion backend: litellm (default), openrouter (OpenRouter preset), "
            "or openai (OpenAI SDK only)."
        ),
    )
    openai_api_key: str = ""
    llm_api_key: str = Field(
        default="",
        description="Generic LLM API key (takes precedence over openai_api_key).",
    )
    llm_base_url: str = Field(
        default="",
        description=(
            "Optional API base URL. For OpenRouter, defaults are applied when empty. "
            "Examples: https://openrouter.ai/api/v1, https://api.groq.com/openai/v1"
        ),
    )
    llm_model: str = Field(
        default="gpt-4o",
        description=(
            "Model id. With openrouter provider use OpenRouter ids "
            "(e.g. anthropic/claude-sonnet-4). With litellm use any LiteLLM model string."
        ),
    )
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096

    @property
    def effective_api_key(self) -> str:
        """Return the active API key (llm_api_key takes precedence)."""
        return self.llm_api_key or self.openai_api_key or ""

    # --- Knowledge / RAG ---
    knowledge_dir: Path = Path("knowledge_base")
    chroma_persist_dir: Path = Path(".chroma_db")
    chroma_collection: str = "oh_knowledge"
    retrieval_top_k: int = 8
    chunk_size: int = 800
    chunk_overlap: int = 200
    ingest_on_startup: bool = Field(
        default=True,
        description="Ingest knowledge_base on startup. Set false on Railway to boot faster.",
    )

    # --- Audit ---
    audit_log_file: Path = Path("logs/audit.jsonl")


def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
