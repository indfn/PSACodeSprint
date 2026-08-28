"""Tool schema adapter — translates tool schemas between provider families.

OpenAI-compatible families (openai, deepseek, ollama, vllm, lmstudio, custom)
use OpenAI's `tools` format directly.
Anthropic uses `input_schema` instead of `parameters`.
Gemini uses `functionDeclarations` style but our abstraction normalises to same flat shape.

The `adapt_tools_for_provider` function is used before each `provider.chat()` call
to ensure the LLM receives tool definitions in its expected format.

Reference: PLAN.md 4.3, REQUIREMENTS.md F-08
"""

from __future__ import annotations

from typing import Any


def _normalise(schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise schemas to flat intermediate {name, description, parameters}.

    Accepts:
      - OpenAI format: {"type": "function", "function": {"name": ..., "parameters": {...}}}
      - Flat format: {"name": ..., "description": ..., "parameters": {...}}
    """
    flat: list[dict[str, Any]] = []
    for s in schemas:
        if "function" in s:
            fn = s["function"]
            flat.append({
                "name": fn["name"],
                "description": fn.get("description", ""),
                "parameters": fn.get("parameters", {}),
            })
        else:
            flat.append({
                "name": s["name"],
                "description": s.get("description", ""),
                "parameters": s.get("parameters", {}),
            })
    return flat


def adapt_tools_for_provider(schemas: list[dict[str, Any]], provider: str) -> list[dict[str, Any]]:
    """Convert OpenAI-format tool schemas to provider-specific format.

    Args:
        schemas: List of tool schemas. Each may be either
                 OpenAI format {"type":"function","function":{...}} or
                 flat {"name":..., "description":..., "parameters":{...}}.
        provider: Provider family name — one of the 8 registry keys:
                  anthropic, openai, gemini, deepseek, ollama, vllm, lmstudio, custom.

    Returns:
        List of provider-specific tool dicts.
        - anthropic: [{name, description, input_schema}]
        - gemini:    [{name, description, parameters}]
        - openai/deepseek/ollama/vllm/lmstudio/custom: OpenAI tools format
    """
    if not schemas:
        return []

    flat = _normalise(schemas)

    if provider == "anthropic":
        # Anthropic expects input_schema instead of parameters
        return [
            {"name": s["name"], "description": s["description"], "input_schema": s["parameters"]}
            for s in flat
        ]
    elif provider == "gemini":
        # Gemini uses functionDeclarations — flat name/description/parameters
        return [
            {"name": s["name"], "description": s["description"], "parameters": s["parameters"]}
            for s in flat
        ]
    else:
        # All OpenAI-compatible families use OpenAI tools format directly — no translation
        return [
            {"type": "function", "function": {"name": s["name"], "description": s["description"], "parameters": s["parameters"]}}
            for s in flat
        ]
