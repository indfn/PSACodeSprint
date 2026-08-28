"""
Custom LLM Provider Abstraction — Provider-Agnostic AI Architecture

Swap between Anthropic, OpenAI, Gemini, DeepSeek, Ollama, vLLM, LM Studio,
or any OpenAI-compatible API via YAML config.

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

Supported providers:
  - anthropic:  Claude (claude-sonnet-4, claude-opus-4, etc.)
  - openai:     GPT-4o, GPT-4o-mini, o1, etc.
  - gemini:     Gemini 2.0 Flash, Gemini 2.5 Pro, etc.
  - deepseek:   DeepSeek V3, DeepSeek R1, etc.
  - ollama:     Any model served by Ollama (local)
  - vllm:       Any model served by vLLM (local/remote)
  - lmstudio:   Any model served by LM Studio (local)
  - custom:     Any OpenAI-compatible API (OpenRouter, Together, Groq, etc.)
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

    def chat_with_retry(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> LLMResponse:
        """Chat with automatic retry on transient failures.

        Args:
            messages: List of message dicts.
            tools: Optional tool schemas.
            temperature: Sampling temperature.
            max_tokens: Max tokens in response.
            max_retries: Maximum retry attempts (default 3).
            retry_delay: Base delay between retries in seconds (doubles each retry).

        Returns:
            LLMResponse from the successful attempt.
        """
        import traceback

        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                return self.chat(messages, tools=tools, temperature=temperature, max_tokens=max_tokens)
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    delay = retry_delay * (2 ** attempt)
                    logger.warning(
                        "Provider %s attempt %d/%d failed: %s — retrying in %.1fs",
                        self.name, attempt + 1, max_retries, exc, delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "Provider %s failed after %d attempts: %s\n%s",
                        self.name, max_retries, exc, traceback.format_exc(),
                    )
        raise last_exc  # type: ignore[misc]

    def health_check(self) -> bool:
        """Check if the provider is reachable and configured.

        Lazy check: validates API key is set, then attempts a minimal
        request. Caches result to avoid repeated network calls.
        """
        if not self._health_checked:
            try:
                self.chat([{"role": "user", "content": "ping"}], max_tokens=5)
                self._health_ok = True
            except Exception:
                self._health_ok = False
            self._health_checked = True
        return self._health_ok

    _health_checked: bool = False
    _health_ok: bool = False


# ---------------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------------

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    name = "anthropic"

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-20250514", base_url: str | None = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self.base_url = base_url
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

        kwargs: dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        client = anthropic.Anthropic(**kwargs)

        # Anthropic uses separate system message
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append({"role": msg["role"], "content": msg["content"]})

        # Convert tools to Anthropic format — handle both OpenAI format and flat/adapted format
        anthropic_tools = []
        if tools:
            for tool in tools:
                if "function" in tool:
                    anthropic_tools.append({
                        "name": tool["function"]["name"],
                        "description": tool["function"].get("description", ""),
                        "input_schema": tool["function"].get("parameters", {}),
                    })
                elif "input_schema" in tool:
                    # Already adapted to anthropic
                    anthropic_tools.append(tool)
                elif "name" in tool:
                    # Flat format {name, description, parameters}
                    anthropic_tools.append({
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "input_schema": tool.get("parameters", tool.get("input_schema", {})),
                    })
                else:
                    continue

        t0 = time.monotonic()
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
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
            finish_reason=str(response.stop_reason or "stop"),
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

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o", base_url: str | None = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.base_url = base_url
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

        client_kwargs: dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        client = openai.OpenAI(**client_kwargs)

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
        from google import genai

        client = genai.Client(api_key=self.api_key)

        # Convert messages to Gemini format
        contents = []
        system_instruction = None
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
                continue
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [msg["content"]]})

        # Convert tools to Gemini format (flat list) — handle OpenAI, flat, and already-adapted
        gemini_tools = []
        if tools:
            function_declarations = []
            for tool in tools:
                if "function" in tool:
                    fn = tool["function"]
                    function_declarations.append({
                        "name": fn["name"],
                        "description": fn.get("description", ""),
                        "parameters": fn.get("parameters", {}),
                    })
                elif "name" in tool:
                    function_declarations.append({
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", tool.get("input_schema", {})),
                    })
                else:
                    continue
            gemini_tools = [{"function_declarations": function_declarations}]

        config = genai.types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
            tools=gemini_tools if gemini_tools else None,
        )

        t0 = time.monotonic()
        response = client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
        latency_ms = (time.monotonic() - t0) * 1000

        content = response.text if response.text else None
        tool_calls = []

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    tool_calls.append({
                        "id": f"gemini_{part.function_call.name}",
                        "type": "function",
                        "function": {
                            "name": part.function_call.name,
                            "arguments": json.dumps(part.function_call.args or {}),
                        },
                    })

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason="stop",
            usage={
                "input_tokens": (
                    response.usage_metadata.prompt_token_count
                    if response.usage_metadata and response.usage_metadata.prompt_token_count is not None
                    else 0
                ),
                "output_tokens": (
                    response.usage_metadata.candidates_token_count
                    if response.usage_metadata and response.usage_metadata.candidates_token_count is not None
                    else 0
                ),
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

    def __init__(self, api_key: str | None = None, model: str = "deepseek-chat", base_url: str | None = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.model = model
        self.base_url = base_url or "https://api.deepseek.com"
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
# Custom / OpenAI-compatible (Ollama, vLLM, LM Studio, OpenRouter, etc.)
# ---------------------------------------------------------------------------

class CustomProvider(LLMProvider):
    """Any OpenAI-compatible API — Ollama, vLLM, LM Studio, OpenRouter, Together, Groq, etc.

    Uses the OpenAI Python client with a custom base_url. Works with any
    server that implements the OpenAI chat completions API.

    YAML config:
        llm:
          provider: custom
          model: llama3.1:8b
          base_url: http://localhost:11434/v1  # Ollama
          api_key: ollama                        # dummy key for Ollama
          # OR:
          base_url: http://localhost:8000/v1     # vLLM
          api_key: token-abc123
          # OR:
          base_url: https://openrouter.ai/api/v1  # OpenRouter
          api_key: sk-or-...
    """

    name = "custom"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "",
        base_url: str = "http://localhost:11434/v1",
    ):
        self.api_key = api_key or os.environ.get("CUSTOM_API_KEY", "dummy")
        self.model = model
        self.base_url = base_url.rstrip("/")
        if not self.model:
            logger.warning("CustomProvider: no model specified — server will use its default")

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

        try:
            response = client.chat.completions.create(**kwargs)
        except openai.APIConnectionError as exc:
            logger.error("Custom provider connection failed (%s): %s", self.base_url, exc)
            raise
        except openai.APIError as exc:
            logger.error("Custom provider API error: %s", exc)
            raise

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
            model=self.model or "default",
            provider=f"custom ({self.base_url})",
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
    "ollama": CustomProvider,       # Ollama is OpenAI-compatible
    "vllm": CustomProvider,         # vLLM is OpenAI-compatible
    "lmstudio": CustomProvider,     # LM Studio is OpenAI-compatible
    "custom": CustomProvider,       # Generic OpenAI-compatible
}


def create_provider(config: dict[str, Any]) -> LLMProvider:
    """Create an LLM provider from YAML config dict.

    Config shape:
        llm:
          provider: anthropic          # or openai, gemini, deepseek, ollama, vllm, lmstudio, custom
          model: claude-sonnet-4-20250514
          api_key_env: ANTHROPIC_API_KEY  # env var name (optional)
          api_key: sk-...                # direct key (optional, overrides env)
          base_url: http://localhost:11434/v1  # for custom/ollama/vllm
          fallback_provider: openai
          fallback_model: gpt-4o

    Supported provider values:
      - anthropic:  Claude models (requires ANTHROPIC_API_KEY)
      - openai:     GPT models (requires OPENAI_API_KEY)
      - gemini:     Gemini models (requires GOOGLE_API_KEY)
      - deepseek:   DeepSeek models (requires DEEPSEEK_API_KEY)
      - ollama:     Local Ollama server (default: http://localhost:11434/v1)
      - vllm:       vLLM server (default: http://localhost:8000/v1)
      - lmstudio:   LM Studio server (default: http://localhost:1234/v1)
      - custom:     Any OpenAI-compatible API (requires base_url)

    Args:
        config: Dict with 'provider', 'model', optional 'api_key', 'base_url'.

    Returns:
        Configured LLMProvider instance.

    Raises:
        ValueError: If provider name is not in the registry.
    """
    provider_name = config.get("provider", "anthropic")
    model = config.get("model", "")
    api_key_env = config.get("api_key_env", "")
    api_key = config.get("api_key") or (os.environ.get(api_key_env, "") if api_key_env else "")
    base_url = config.get("base_url", "")

    if provider_name not in PROVIDERS:
        raise ValueError(
            f"Unknown provider '{provider_name}'. "
            f"Available: {list(PROVIDERS.keys())}"
        )

    provider_cls = PROVIDERS[provider_name]
    kwargs: dict[str, Any] = {}

    # All custom/ollama/vllm/lmstudio providers use CustomProvider
    if provider_name in ("ollama", "vllm", "lmstudio", "custom"):
        if not base_url:
            # Default URLs per provider type
            defaults = {
                "ollama": "http://localhost:11434/v1",
                "vllm": "http://localhost:8000/v1",
                "lmstudio": "http://localhost:1234/v1",
                "custom": "",
            }
            base_url = defaults.get(provider_name, "")
        kwargs["base_url"] = base_url
        if api_key:
            kwargs["api_key"] = api_key
        if model:
            kwargs["model"] = model
    else:
        # Named providers (anthropic, openai, gemini, deepseek)
        if api_key:
            kwargs["api_key"] = api_key
        if model:
            kwargs["model"] = model
        if base_url:
            kwargs["base_url"] = base_url

    provider = provider_cls(**kwargs)
    logger.info("Created LLM provider: %s (model: %s)", provider_name, model or "default")

    return provider


def create_provider_with_fallback(config: dict[str, Any]) -> LLMProvider:
    """Create provider with optional fallback.

    If the primary provider fails on health check, try the fallback.

    Config shape:
        llm:
          provider: ollama
          model: llama3.1:8b
          base_url: http://localhost:11434/v1
          fallback_provider: openai
          fallback_model: gpt-4o
          fallback_api_key_env: OPENAI_API_KEY
    """
    primary = create_provider(config)

    fallback_name = config.get("fallback_provider")
    if fallback_name:
        fallback_config = {
            "provider": fallback_name,
            "model": config.get("fallback_model", ""),
            "api_key_env": config.get("fallback_api_key_env", ""),
            "api_key": config.get("fallback_api_key", ""),
            "base_url": config.get("fallback_base_url", ""),
        }
        fallback = create_provider(fallback_config)

        if not primary.health_check():
            logger.warning(
                "Primary provider %s failed health check, using fallback %s",
                primary.name, fallback.name,
            )
            return fallback

    return primary
