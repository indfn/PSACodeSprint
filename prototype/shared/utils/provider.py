"""
Custom LLM Provider Abstraction — Provider-Agnostic AI Architecture

Swap between Anthropic, OpenAI, Gemini, and DeepSeek via YAML config.
Unified chat interface, optional fallback provider, response tracking.

Tech Stack ref: Section 4 (LLM Provider Abstraction), Section 8 (YAML config)

Usage:
    from shared.utils.provider import LLMProvider, create_provider

    # From YAML config
    provider = create_provider(config["llm"])
    response = provider.chat(
        messages=[{"role": "user", "content": "Compute ITT split"}],
        tools=[tool_schema_1, tool_schema_2],
    )
"""

from __future__ import annotations

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------

@dataclass
class LLMResponse:
    """Unified response from any LLM provider."""

    content: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)
    model: str = ""
    provider: str = ""
    latency_ms: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    @property
    def input_tokens(self) -> int:
        return self.usage.get("input_tokens", 0)

    @property
    def output_tokens(self) -> int:
        return self.usage.get("output_tokens", 0)


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All providers implement the same chat() interface. The agent calls
    provider.chat() without knowing which backend is active.
    """

    name: str = "base"

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a chat request to the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: Optional list of tool schemas (OpenAI function-calling format).
            temperature: Sampling temperature (0.0 = deterministic).
            max_tokens: Maximum tokens in the response.

        Returns:
            LLMResponse with content, tool_calls, usage, and timing.
        """
        ...

    def health_check(self) -> bool:
        """Check if the provider is reachable and configured."""
        try:
            self.chat([{"role": "user", "content": "ping"}], max_tokens=5)
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------------

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    name = "anthropic"

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        if not self.api_key:
            logger.warning("Anthropic API key not set — provider will fail on chat()")

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)

        # Anthropic uses separate system message
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append({"role": msg["role"], "content": msg["content"]})

        # Convert tools to Anthropic format
        anthropic_tools = []
        if tools:
            for tool in tools:
                anthropic_tools.append({
                    "name": tool["function"]["name"],
                    "description": tool["function"].get("description", ""),
                    "input_schema": tool["function"].get("parameters", {}),
                })

        t0 = time.monotonic()
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_msg,
            messages=chat_messages,
            tools=anthropic_tools if anthropic_tools else [],
        )
        latency_ms = (time.monotonic() - t0) * 1000

        # Parse response
        content = None
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input),
                    },
                })

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            model=self.model,
            provider=self.name,
            latency_ms=latency_ms,
            raw=response.model_dump(),
        )


# ---------------------------------------------------------------------------
# OpenAI (GPT-4o)
# ---------------------------------------------------------------------------

class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    name = "openai"

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        if not self.api_key:
            logger.warning("OpenAI API key not set — provider will fail on chat()")

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        import openai

        client = openai.OpenAI(api_key=self.api_key)

        t0 = time.monotonic()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        response = client.chat.completions.create(**kwargs)
        latency_ms = (time.monotonic() - t0) * 1000

        choice = response.choices[0]
        content = choice.message.content
        tool_calls = []

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            model=self.model,
            provider=self.name,
            latency_ms=latency_ms,
            raw=response.model_dump(),
        )


# ---------------------------------------------------------------------------
# Google Gemini
# ---------------------------------------------------------------------------

class GeminiProvider(LLMProvider):
    """Google Gemini provider."""

    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        self.model = model
        if not self.api_key:
            logger.warning("Google API key not set — provider will fail on chat()")

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)

        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] in ("user", "tool") else "model"
            contents.append({"role": role, "parts": [msg["content"]]})

        # Convert tools to Gemini format
        gemini_tools = []
        if tools:
            for tool in tools:
                fn = tool["function"]
                gemini_tools.append({
                    "function_declarations": [{
                        "name": fn["name"],
                        "description": fn.get("description", ""),
                        "parameters": fn.get("parameters", {}),
                    }]
                })

        t0 = time.monotonic()
        response = model.generate_content(
            contents,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
            tools=gemini_tools if gemini_tools else None,
        )
        latency_ms = (time.monotonic() - t0) * 1000

        content = response.text if response.text else None
        tool_calls = []

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    tool_calls.append({
                        "id": f"gemini_{part.function_call.name}",
                        "type": "function",
                        "function": {
                            "name": part.function_call.name,
                            "arguments": json.dumps(dict(part.function_call.args)),
                        },
                    })

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason="stop",
            usage={
                "input_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
            },
            model=self.model,
            provider=self.name,
            latency_ms=latency_ms,
            raw={"candidates": str(response.candidates)} if response.candidates else {},
        )


# ---------------------------------------------------------------------------
# DeepSeek
# ---------------------------------------------------------------------------

class DeepSeekProvider(LLMProvider):
    """DeepSeek provider (OpenAI-compatible API)."""

    name = "deepseek"

    def __init__(self, api_key: str | None = None, model: str = "deepseek-chat"):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.model = model
        self.base_url = "https://api.deepseek.com"
        if not self.api_key:
            logger.warning("DeepSeek API key not set — provider will fail on chat()")

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        import openai

        client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)

        t0 = time.monotonic()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        response = client.chat.completions.create(**kwargs)
        latency_ms = (time.monotonic() - t0) * 1000

        choice = response.choices[0]
        content = choice.message.content
        tool_calls = []

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            model=self.model,
            provider=self.name,
            latency_ms=latency_ms,
            raw=response.model_dump(),
        )


# ---------------------------------------------------------------------------
# Provider registry + factory
# ---------------------------------------------------------------------------

PROVIDERS: dict[str, type[LLMProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "deepseek": DeepSeekProvider,
}


def create_provider(config: dict[str, Any]) -> LLMProvider:
    """Create an LLM provider from YAML config dict.

    Config shape:
        llm:
          provider: anthropic
          model: claude-sonnet-4-20250514
          api_key_env: ANTHROPIC_API_KEY
          fallback_provider: openai
          fallback_model: gpt-4o

    Args:
        config: Dict with 'provider', 'model', optional 'api_key_env'.

    Returns:
        Configured LLMProvider instance.

    Raises:
        ValueError: If provider name is not in the registry.
    """
    provider_name = config.get("provider", "anthropic")
    model = config.get("model", "")
    api_key_env = config.get("api_key_env", "")
    api_key = os.environ.get(api_key_env, "") if api_key_env else ""

    if provider_name not in PROVIDERS:
        raise ValueError(
            f"Unknown provider '{provider_name}'. "
            f"Available: {list(PROVIDERS.keys())}"
        )

    provider_cls = PROVIDERS[provider_name]
    kwargs = {}
    if api_key:
        kwargs["api_key"] = api_key
    if model:
        kwargs["model"] = model

    provider = provider_cls(**kwargs)
    logger.info("Created LLM provider: %s (model: %s)", provider_name, model)

    return provider


def create_provider_with_fallback(config: dict[str, Any]) -> LLMProvider:
    """Create provider with optional fallback.

    If the primary provider fails on health check, try the fallback.
    """
    primary = create_provider(config)

    fallback_name = config.get("fallback_provider")
    if fallback_name:
        fallback_config = {
            "provider": fallback_name,
            "model": config.get("fallback_model", ""),
            "api_key_env": config.get("fallback_api_key_env", ""),
        }
        fallback = create_provider(fallback_config)

        if not primary.health_check():
            logger.warning(
                "Primary provider %s failed health check, using fallback %s",
                primary.name, fallback.name,
            )
            return fallback

    return primary
