"""System prompt builder — templated from ProblemConfig (Phase 6.2).

Not hardcoded to PB-12. Works for any C2 problem by rendering the
currently active ProblemConfig into the system instruction.
"""

from __future__ import annotations

from typing import Any


def build_system_prompt(config: Any) -> str:
    """Build system prompt from a ProblemConfig (or dict-like).

    Accepts ProblemConfig dataclass or dict with .problem/.systems/.tools.
    """
    # Normalise config access
    if isinstance(config, dict):
        problem = config.get("problem", {})
        pid = problem.get("id", "unknown") if isinstance(problem, dict) else getattr(problem, "id", "unknown")
        pname = problem.get("name", "") if isinstance(problem, dict) else getattr(problem, "name", "")
        sector = problem.get("sector", "") if isinstance(problem, dict) else getattr(problem, "sector", "")
        description = problem.get("description", "") if isinstance(problem, dict) else getattr(problem, "description", "")
        systems = config.get("systems", [])
        tools = config.get("tools", [])
        cost_params = config.get("cost_params", {})
        escalation_triggers = config.get("escalation_triggers", [])
        confidence = config.get("confidence", {})
    else:
        pid = getattr(getattr(config, "problem", None), "id", "unknown")
        pname = getattr(getattr(config, "problem", None), "name", "")
        sector = getattr(getattr(config, "problem", None), "sector", "")
        description = getattr(getattr(config, "problem", None), "description", "")
        systems = getattr(config, "systems", []) or []
        tools = getattr(config, "tools", []) or []
        cost_params = getattr(config, "cost_params", {}) or {}
        escalation_triggers = getattr(config, "escalation_triggers", []) or []
        conf_obj = getattr(config, "confidence", None)
        if conf_obj is not None and not isinstance(conf_obj, dict):
            confidence = {"threshold": getattr(conf_obj, "threshold", 0.85), "method": getattr(conf_obj, "method", "llm_self_assessment")}
        else:
            confidence = conf_obj or {}

    # Render systems and tools lists
    def _system_names(sys_list) -> str:
        names = []
        for s in sys_list:
            if isinstance(s, dict):
                names.append(s.get("name", str(s)))
            else:
                names.append(getattr(s, "name", str(s)))
        return ", ".join(names) if names else "none"

    def _tool_names(tool_list) -> str:
        names = []
        for t in tool_list:
            if isinstance(t, dict):
                if t.get("type") == "event_trigger":
                    continue
                names.append(t.get("name", str(t)))
            else:
                if getattr(t, "type", None) == "event_trigger":
                    continue
                names.append(getattr(t, "name", str(t)))
        return ", ".join(names) if names else "none"

    def _escalation_text(triggers) -> str:
        lines = []
        for e in triggers:
            if isinstance(e, dict):
                lines.append(f"- {e.get('name','')} ({e.get('trigger_id','')}): {e.get('condition','')} threshold={e.get('threshold','')}")
            else:
                lines.append(f"- {getattr(e,'name','')} ({getattr(e,'trigger_id','')}): {getattr(e,'condition','')} threshold={getattr(e,'threshold','')}")
        return "\n".join(lines) if lines else "none"

    threshold = confidence.get("threshold", 0.85) if isinstance(confidence, dict) else 0.85

    system_names = _system_names(systems)
    tool_names = _tool_names(tools)
    escalation_text = _escalation_text(escalation_triggers)

    return f"""You are PSA Nexus — an agentic coordinator for PSA Singapore port operations.

Problem: {pname} ({pid}) — sector: {sector}
Description: {description}

Available systems: {system_names}
Available tools: {tool_names}
Cost params: {cost_params}

Escalation triggers (charter §4):
{escalation_text}

Rules:
- Reason step-by-step. Select the minimal next tool(s) that advance the charter workflow.
- When you have a recommendation (e.g. split computed), generate an approval card and set hitl_pending.
- If confidence < {threshold}, request HITL approval (Trigger #1 — low confidence).
- If any escalation trigger fires, set escalation and HITL-5 (Escalate to Duty Manager).
- Output confidence as 0.0–1.0 in structured JSON alongside your reasoning.
- Output tool_calls as structured JSON with name and arguments.
- Never hallucinate tool names. Only use tools listed above (from the active problem's tool registry).
- Validate inputs: check weight_bounds, block capacity, truck availability, feeder capacity, vessel margin, tidal window before proposing a split.
"""

# Backwards compatibility: expose SYSTEM_PROMPT as legacy constant for tests that import it
try:
    from app.configs.problem_config import load_problem_config
    _default_cfg = load_problem_config("pb-12-itt")
    SYSTEM_PROMPT = build_system_prompt(_default_cfg)
except Exception:
    SYSTEM_PROMPT = "You are PSA Nexus — an agentic coordinator for PSA Singapore."


def build_agent_messages(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Build full message list for LLM call: system + history."""
    cfg = state.get("problem_config") or state.get("problem_id") or {}
    # If problem_config is not yet loaded, try to load by problem_id
    if isinstance(cfg, str):
        try:
            from app.configs.problem_config import load_problem_config
            cfg = load_problem_config(cfg)
        except Exception:
            cfg = {}
    elif cfg == {} or cfg is None:
        try:
            from app.configs.problem_config import load_problem_config
            from app.agent.problem_switcher import get_active_problem_id
            cfg = load_problem_config(get_active_problem_id())
        except Exception:
            cfg = {}

    system = build_system_prompt(cfg) if cfg else SYSTEM_PROMPT
    messages = [{"role": "system", "content": system}]
    history = state.get("messages", []) or []
    # Ensure history is a list
    if isinstance(history, list):
        messages.extend(history)
    return messages
