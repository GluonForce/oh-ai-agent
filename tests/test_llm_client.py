"""Tests for LLM client configuration and model resolution."""

from __future__ import annotations

import pytest

from oh_agent.agents.llm_client import (
    LiteLLMChatClient,
    OpenAISDKChatClient,
    create_llm_client,
    resolve_model,
)
from oh_agent.config import LLMProvider, Settings


class TestResolveModel:
    def test_litellm_uses_model_unchanged(self) -> None:
        settings = Settings(llm_provider=LLMProvider.LITELLM, llm_model="gpt-4o")
        assert resolve_model(settings) == "gpt-4o"

    def test_litellm_openrouter_prefix_passthrough(self) -> None:
        settings = Settings(
            llm_provider=LLMProvider.LITELLM,
            llm_model="openrouter/anthropic/claude-sonnet-4",
        )
        assert resolve_model(settings) == "openrouter/anthropic/claude-sonnet-4"

    def test_openrouter_provider_prefixes_model(self) -> None:
        settings = Settings(
            llm_provider=LLMProvider.OPENROUTER,
            llm_model="anthropic/claude-sonnet-4",
        )
        assert resolve_model(settings) == "openrouter/anthropic/claude-sonnet-4"

    def test_openrouter_provider_keeps_existing_prefix(self) -> None:
        settings = Settings(
            llm_provider=LLMProvider.OPENROUTER,
            llm_model="openrouter/meta-llama/llama-3.3-70b-instruct",
        )
        assert resolve_model(settings) == "openrouter/meta-llama/llama-3.3-70b-instruct"


class TestCreateLLMClient:
    def test_default_is_litellm(self) -> None:
        client = create_llm_client(Settings())
        assert isinstance(client, LiteLLMChatClient)

    def test_openai_provider_uses_sdk(self) -> None:
        client = create_llm_client(Settings(llm_provider=LLMProvider.OPENAI))
        assert isinstance(client, OpenAISDKChatClient)

    def test_openrouter_resolved_model(self) -> None:
        client = create_llm_client(
            Settings(llm_provider=LLMProvider.OPENROUTER, llm_model="google/gemini-2.0-flash-001")
        )
        assert client.resolved_model == "openrouter/google/gemini-2.0-flash-001"


class TestLiteLLMComplete:
    def test_complete_returns_message_content(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class FakeMessage:
            content = '{"ok": true}'

        class FakeChoice:
            message = FakeMessage()

        class FakeResponse:
            choices = [FakeChoice()]

        def fake_completion(**kwargs: object) -> FakeResponse:
            assert kwargs["model"] == "openrouter/anthropic/claude-sonnet-4"
            assert kwargs["api_base"] == "https://openrouter.ai/api/v1"
            return FakeResponse()

        import litellm

        monkeypatch.setattr(litellm, "completion", fake_completion)

        client = LiteLLMChatClient(
            Settings(
                llm_provider=LLMProvider.OPENROUTER,
                llm_model="anthropic/claude-sonnet-4",
                llm_api_key="sk-or-test",
            )
        )
        assert client.complete([{"role": "user", "content": "hi"}]) == '{"ok": true}'
