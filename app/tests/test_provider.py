"""Tests for provider + tool adapter (F-03, F-08). Covers all 8 provider names."""

import os
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.shared.provider import (
    PROVIDERS,
    CustomProvider,
    create_provider,
    create_provider_with_fallback,
)
from app.shared.tool_adapter import adapt_tools_for_provider


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

def test_providers_registry_has_8():
    assert len(PROVIDERS) == 8
    assert set(PROVIDERS.keys()) == {"anthropic", "openai", "gemini", "deepseek", "ollama", "vllm", "lmstudio", "custom"}


@pytest.mark.parametrize("provider_name", list(PROVIDERS.keys()))
def test_create_provider_no_key_error(provider_name):
    cfg = {"provider": provider_name, "model": "test-model", "api_key": "dummy-key"}
    if provider_name in ("ollama", "vllm", "lmstudio", "custom"):
        cfg["base_url"] = "http://localhost:11434/v1"
    p = create_provider(cfg)
    assert p is not None
    # ollama/vllm/lmstudio/custom all use CustomProvider
    if provider_name in ("ollama", "vllm", "lmstudio", "custom"):
        assert isinstance(p, CustomProvider)


def test_create_provider_unknown_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        create_provider({"provider": "unknown", "model": "x"})


def test_create_provider_uses_env_var(monkeypatch):
    monkeypatch.setenv("MY_API_KEY", "env-key-123")
    p = create_provider({"provider": "openai", "model": "gpt-4o", "api_key_env": "MY_API_KEY"})
    assert p.api_key == "env-key-123"


def test_custom_provider_default_urls():
    # ollama without base_url should get default
    p = create_provider({"provider": "ollama", "model": "llama3.1:8b", "api_key": "ollama"})
    assert p.base_url == "http://localhost:11434/v1"
    p2 = create_provider({"provider": "vllm", "model": "m", "api_key": "k"})
    assert p2.base_url == "http://localhost:8000/v1"
    p3 = create_provider({"provider": "lmstudio", "model": "m", "api_key": "k"})
    assert p3.base_url == "http://localhost:1234/v1"


# ---------------------------------------------------------------------------
# CustomProvider with base_url
# ---------------------------------------------------------------------------

def test_custom_provider_base_url_and_api_key():
    p = CustomProvider(api_key="sk-or-123", model="anthropic/claude-sonnet-4", base_url="https://openrouter.ai/api/v1")
    assert p.base_url == "https://openrouter.ai/api/v1"
    assert p.model == "anthropic/claude-sonnet-4"


# ---------------------------------------------------------------------------
# create_provider_with_fallback
# ---------------------------------------------------------------------------

def test_create_provider_with_fallback_primary_ok():
    # primary health_check mocked to succeed → returns primary
    cfg = {
        "provider": "openai",
        "model": "gpt-4o",
        "api_key": "dummy",
        "fallback_provider": "anthropic",
        "fallback_model": "claude-sonnet-4-20250514",
        "fallback_api_key": "dummy2",
    }
    with patch("app.shared.provider.OpenAIProvider.health_check", return_value=True):
        p = create_provider_with_fallback(cfg)
        assert p.name == "openai"


def test_create_provider_with_fallback_uses_fallback():
    cfg = {
        "provider": "ollama",
        "model": "llama3.1:8b",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "fallback_provider": "openai",
        "fallback_model": "gpt-4o",
        "fallback_api_key": "dummy",
    }
    with patch("app.shared.provider.CustomProvider.health_check", return_value=False):
        p = create_provider_with_fallback(cfg)
        assert p.name == "openai"


# ---------------------------------------------------------------------------
# chat with tool_calls (mocked)
# ---------------------------------------------------------------------------

def test_openai_chat_with_tool_calls_mocked():
    cfg = {"provider": "openai", "model": "gpt-4o", "api_key": "test-key"}
    provider = create_provider(cfg)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "thinking"
    mock_choice = mock_response.choices[0]
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_123"
    mock_tool_call.type = "function"
    mock_tool_call.function.name = "get_itt_candidates"
    mock_tool_call.function.arguments = '{"vessel_id": "MV PACIFIC STAR"}'
    mock_choice.message.tool_calls = [mock_tool_call]
    mock_choice.finish_reason = "tool_calls"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.model_dump.return_value = {"id": "chatcmpl-123"}

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client):
        tools = [{"type": "function", "function": {"name": "get_itt_candidates", "description": "test", "parameters": {"type": "object"}}}]
        resp = provider.chat([{"role": "user", "content": "hello"}], tools=tools)
        assert resp.has_tool_calls
        assert resp.tool_calls[0]["function"]["name"] == "get_itt_candidates"
        assert resp.usage["input_tokens"] == 10
        assert resp.provider == "openai"


def test_anthropic_chat_with_tool_calls_mocked():
    cfg = {"provider": "anthropic", "model": "claude-sonnet-4-20250514", "api_key": "test-key"}
    provider = create_provider(cfg)

    mock_block_text = MagicMock()
    mock_block_text.type = "text"
    mock_block_text.text = "thinking"
    mock_block_tool = MagicMock()
    mock_block_tool.type = "tool_use"
    mock_block_tool.id = "toolu_123"
    mock_block_tool.name = "get_itt_candidates"
    mock_block_tool.input = {"vessel_id": "MV PACIFIC STAR"}

    mock_response = MagicMock()
    mock_response.content = [mock_block_text, mock_block_tool]
    mock_response.stop_reason = "tool_use"
    mock_response.usage.input_tokens = 10
    mock_response.usage.output_tokens = 5
    mock_response.model_dump.return_value = {"id": "msg_123"}

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("anthropic.Anthropic", return_value=mock_client):
        tools = [{"type": "function", "function": {"name": "get_itt_candidates", "description": "test", "parameters": {"type": "object"}}}]
        resp = provider.chat([{"role": "user", "content": "hello"}], tools=tools)
        assert resp.has_tool_calls
        assert resp.tool_calls[0]["function"]["name"] == "get_itt_candidates"
        assert resp.provider == "anthropic"


def test_custom_chat_with_tool_calls_mocked():
    cfg = {"provider": "custom", "model": "llama3.1:8b", "base_url": "http://localhost:11434/v1", "api_key": "ollama"}
    provider = create_provider(cfg)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_custom"
    mock_tool_call.type = "function"
    mock_tool_call.function.name = "check_road_itt_capacity"
    mock_tool_call.function.arguments = '{}'
    mock_response.choices[0].message.tool_calls = [mock_tool_call]
    mock_response.choices[0].finish_reason = "tool_calls"
    mock_response.usage.prompt_tokens = 8
    mock_response.usage.completion_tokens = 4
    mock_response.model_dump.return_value = {}

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client):
        tools = [{"type": "function", "function": {"name": "check_road_itt_capacity", "description": "test", "parameters": {"type": "object"}}}]
        resp = provider.chat([{"role": "user", "content": "hello"}], tools=tools)
        assert resp.has_tool_calls
        assert "custom" in resp.provider


def test_health_check_mocked():
    cfg = {"provider": "openai", "model": "gpt-4o", "api_key": "test-key"}
    provider = create_provider(cfg)
    with patch.object(provider, "chat", return_value=MagicMock()):
        assert provider.health_check() is True
        # second call should use cache
        assert provider.health_check() is True


def test_chat_with_retry_success_after_failure():
    cfg = {"provider": "openai", "model": "gpt-4o", "api_key": "test-key"}
    provider = create_provider(cfg)
    mock_resp = MagicMock()
    mock_resp.content = "ok"
    mock_resp.tool_calls = []
    mock_resp.usage = {}
    # First call raises, second succeeds
    with patch.object(provider, "chat", side_effect=[Exception("transient"), mock_resp]) as mock_chat:
        with patch("time.sleep"):
            result = provider.chat_with_retry([{"role": "user", "content": "hi"}], max_retries=2, retry_delay=0.01)
            assert result.content == "ok"
            assert mock_chat.call_count == 2


# ---------------------------------------------------------------------------
# Tool adapter — 4 families
# ---------------------------------------------------------------------------

def test_adapter_anthropic():
    schemas = [{"name": "get_itt_candidates", "description": "desc", "parameters": {"type": "object", "properties": {"vessel_id": {"type": "string"}}}}]
    adapted = adapt_tools_for_provider(schemas, "anthropic")
    assert adapted[0]["name"] == "get_itt_candidates"
    assert "input_schema" in adapted[0]
    assert adapted[0]["input_schema"] == schemas[0]["parameters"]
    assert "parameters" not in adapted[0]


def test_adapter_gemini():
    schemas = [{"name": "get_itt_candidates", "description": "desc", "parameters": {"type": "object"}}]
    adapted = adapt_tools_for_provider(schemas, "gemini")
    assert adapted[0]["name"] == "get_itt_candidates"
    assert "parameters" in adapted[0]
    assert "input_schema" not in adapted[0]


def test_adapter_openai():
    schemas = [{"name": "get_itt_candidates", "description": "desc", "parameters": {"type": "object"}}]
    adapted = adapt_tools_for_provider(schemas, "openai")
    assert adapted[0]["type"] == "function"
    assert adapted[0]["function"]["name"] == "get_itt_candidates"
    assert "input_schema" not in str(adapted)


def test_adapter_custom_no_op():
    schemas = [{"name": "get_itt_candidates", "description": "desc", "parameters": {"type": "object"}}]
    adapted = adapt_tools_for_provider(schemas, "custom")
    assert adapted[0]["type"] == "function"
    # custom should be same as openai (no translation)
    assert adapt_tools_for_provider(schemas, "custom") == adapt_tools_for_provider(schemas, "openai")
    assert adapt_tools_for_provider(schemas, "ollama") == adapt_tools_for_provider(schemas, "openai")
    assert adapt_tools_for_provider(schemas, "vllm") == adapt_tools_for_provider(schemas, "openai")
    assert adapt_tools_for_provider(schemas, "deepseek") == adapt_tools_for_provider(schemas, "openai")


def test_adapter_empty():
    assert adapt_tools_for_provider([], "anthropic") == []
    assert adapt_tools_for_provider([], "openai") == []


def test_adapter_openai_wrapped_input():
    # Input already in OpenAI wrapper should still work
    wrapped = [{"type": "function", "function": {"name": "get_itt_candidates", "description": "desc", "parameters": {"type": "object"}}}]
    adapted = adapt_tools_for_provider(wrapped, "anthropic")
    assert adapted[0]["name"] == "get_itt_candidates"
    assert "input_schema" in adapted[0]
