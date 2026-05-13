"""LLM client factory supporting multiple OpenAI-compatible backends.

Supports any provider exposing an OpenAI-compatible chat completions API:
- OpenAI (default)
- Anthropic (via their OpenAI-compatible endpoint)
- Azure OpenAI
- OpenRouter, Together, Groq, Fireworks, etc.
- Any custom endpoint (set OH_LLM_BASE_URL)

Configuration priority for API key: OH_LLM_API_KEY > OH_OPENAI_API_KEY
"""

from __future__ import annotations

import logging

from openai import OpenAI

from oh_agent.config import Settings

logger = logging.getLogger(__name__)


def create_llm_client(settings: Settings) -> OpenAI:
    """Build an OpenAI client configured from application settings.

    When ``settings.llm_base_url`` is set the client points at that
    custom endpoint, allowing any OpenAI-compatible provider.
    """
    api_key = settings.effective_api_key or "not-set"
    kwargs: dict[str, str] = {"api_key": api_key}

    if settings.llm_base_url:
        kwargs["base_url"] = settings.llm_base_url
        logger.info(
            "Using custom LLM endpoint: %s (model=%s)",
            settings.llm_base_url,
            settings.llm_model,
        )
    else:
        logger.info("Using default OpenAI endpoint (model=%s)", settings.llm_model)

    return OpenAI(**kwargs)
