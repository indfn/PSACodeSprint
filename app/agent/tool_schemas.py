"""LLM-compatible tool definitions — dynamically reflects current problem's registry (Phase 6.2)."""
from __future__ import annotations

from typing import Any


def get_tool_schemas(problem_id: str | None = None) -> list[dict[str, Any]]:
    """Return LLM tool schemas for the active (or specified) problem.

    Uses ToolRegistry to ensure schemas match the currently registered tool set
    (switched via POST /agent/switch-problem). Falls back to loading by
    problem_id if registry is empty.
    """
    try:
        from app.tools.registry import registry
        if registry.list():
            return registry.get_schemas()
    except Exception:
        pass

    # Fallback: load tools for given problem_id via factory
    if problem_id:
        try:
            from app.tools.registry import load_tools_for_problem
            tools = load_tools_for_problem(problem_id)
            return [t.get_schema() for t in tools]
        except Exception:
            return []

    # Last resort: PB-12
    try:
        from app.tools.registry import load_tools_for_problem
        tools = load_tools_for_problem("pb-12-itt")
        return [t.get_schema() for t in tools]
    except Exception:
        return []


def to_openai_tools_format(schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise flat schemas to OpenAI tools format for provider adapter.

    Each schema may be flat {name, description, parameters} or already
    OpenAI-shaped. This ensures consistent OpenAI format before adaptation.
    """
    out: list[dict[str, Any]] = []
    for s in schemas:
        if "function" in s:
            out.append(s)
        else:
            out.append({
                "type": "function",
                "function": {
                    "name": s.get("name", ""),
                    "description": s.get("description", ""),
                    "parameters": s.get("parameters", s.get("parameters_schema", {})),
                },
            })
    return out
