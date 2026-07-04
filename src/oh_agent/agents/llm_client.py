"""LLM client — LiteLLM-backed with optional OpenAI SDK fallback.

Uses `litellm.completion()` by default so you can switch models via
``OH_LLM_MODEL`` without code changes, including:

- OpenAI: ``gpt-4o``, ``gpt-4o-mini``
- OpenRouter: set ``OH_LLM_PROVIDER=openrouter`` and a model id such as
  ``anthropic/claude-sonnet-4`` (auto-prefixed as ``openrouter/...``)
- Other LiteLLM providers: ``groq/llama-3.3-70b-versatile``, ``azure/...``, etc.

Set ``OH_LLM_PROVIDER=openai`` to use the legacy OpenAI Python SDK only.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Protocol

from oh_agent.config import LLMProvider, Settings

logger = logging.getLogger(__name__)

ChatMessage = dict[str, str]

OPENROUTER_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


class LLMClient(Protocol):
    """Minimal interface used by workflow and benchmark agents."""

    @property
    def resolved_model(self) -> str:
        """Model id sent to the provider (after provider-specific normalisation)."""
        ...

    @property
    def provider(self) -> LLMProvider:
        ...

    def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        ...


def _normalise_base_url(url: str) -> str:
    """Normalise a user-supplied base URL for OpenAI-compatible APIs."""
    url = url.rstrip("/")
    for suffix in ("/chat/completions", "/completions", "/embeddings"):
        if url.endswith(suffix):
            url = url[: -len(suffix)].rstrip("/")
    return url


def resolve_model(settings: Settings) -> str:
    """Return the model string passed to LiteLLM or the OpenAI SDK."""
    model = settings.llm_model.strip()
    if settings.llm_provider == LLMProvider.OPENROUTER:
        if not model.startswith("openrouter/"):
            model = f"openrouter/{model}"
    return model


def _sync_provider_env(settings: Settings) -> None:
    """Expose API keys to LiteLLM via standard provider env vars."""
    key = settings.effective_api_key
    if not key:
        return
    if settings.llm_provider == LLMProvider.OPENROUTER:
        os.environ.setdefault("OPENROUTER_API_KEY", key)
    elif settings.llm_provider == LLMProvider.OPENAI:
        os.environ.setdefault("OPENAI_API_KEY", key)
    else:
        # LiteLLM generic + OpenAI when model has no provider prefix
        os.environ.setdefault("OPENAI_API_KEY", key)


class LiteLLMChatClient:
    """Chat completions via LiteLLM (multi-provider, model-string routing)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model = resolve_model(settings)
        _sync_provider_env(settings)
        if settings.llm_base_url:
            logger.info(
                "LiteLLM client: model=%s api_base=%s",
                self._model,
                _normalise_base_url(settings.llm_base_url),
            )
        else:
            logger.info("LiteLLM client: model=%s (provider=%s)", self._model, settings.llm_provider.value)

    @property
    def resolved_model(self) -> str:
        return self._model

    @property
    def provider(self) -> LLMProvider:
        return self._settings.llm_provider

    def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        import litellm

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self._settings.llm_temperature,
            "max_tokens": max_tokens if max_tokens is not None else self._settings.llm_max_tokens,
        }
        key = self._settings.effective_api_key
        if key:
            kwargs["api_key"] = key
        base_url = self._settings.llm_base_url
        if not base_url and self._settings.llm_provider == LLMProvider.OPENROUTER:
            base_url = OPENROUTER_DEFAULT_BASE_URL
        if base_url:
            kwargs["api_base"] = _normalise_base_url(base_url)
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = litellm.completion(**kwargs)
        content = response.choices[0].message.content
        return content or ""


class OpenAISDKChatClient:
    """Legacy path: OpenAI Python SDK only (``OH_LLM_PROVIDER=openai``)."""

    def __init__(self, settings: Settings) -> None:
        from openai import OpenAI

        self._settings = settings
        self._model = settings.llm_model
        api_key = settings.effective_api_key or "not-set"
        client_kwargs: dict[str, str] = {"api_key": api_key}
        if settings.llm_base_url:
            client_kwargs["base_url"] = _normalise_base_url(settings.llm_base_url)
            logger.info("OpenAI SDK: base_url=%s model=%s", client_kwargs["base_url"], self._model)
        else:
            logger.info("OpenAI SDK: default endpoint model=%s", self._model)
        self._client = OpenAI(**client_kwargs)

    @property
    def resolved_model(self) -> str:
        return self._model

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.OPENAI

    def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        create_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,  # type: ignore[arg-type]
            "temperature": temperature if temperature is not None else self._settings.llm_temperature,
            "max_tokens": max_tokens if max_tokens is not None else self._settings.llm_max_tokens,
        }
        if json_mode:
            create_kwargs["response_format"] = {"type": "json_object"}
        completion = self._client.chat.completions.create(**create_kwargs)
        return completion.choices[0].message.content or ""


def create_llm_client(settings: Settings) -> LLMClient:
    """Build the configured chat client."""
    if settings.llm_provider == LLMProvider.OPENAI:
        return OpenAISDKChatClient(settings)
    return LiteLLMChatClient(settings)
