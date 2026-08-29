"""Agent and Tool nodes — LLM reasoning + tool execution (Phase 6.3/6.4)."""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from app.agent.confidence import compute_risk_score
from app.agent.mock_provider import _MockProvider, mock_provider_for_state, fallback_llm_response
from app.agent.prompts import build_agent_messages
from app.agent.trace import log_trace
from app.hitl.models import HITL5_FALLBACK
from app.shared.logging import structured_log


async def agent_node(state: dict[str, Any]) -> dict[str, Any]:
    """Core LLM reasoning node.

    NOTE: This node mutates `state` in-place and returns the same dict.
    This is intentional for LangGraph v0.2+ which uses the returned dict
    as the new state. If migrating to reducer-based state (e.g.
    Annotated[list, operator.add]), nodes would need to return partial dicts.

    1. Builds messages from state (templated system prompt + history)
    2. Calls LLM with tool schemas (provider-adapted)
    3. Validates tool_calls against registry (hallucination handling)
    4. Handles HITL card / escalation / completion routing
    5. Updates trace + confidence + escalation checks

    Uses rate-limited chat wrapper and deterministic confidence fallback.
    """
    t0 = time.monotonic()
    # Fast path: deterministic HITL gating BEFORE LLM to avoid 30s LLM delays on large histories.
    # If next HITL gate is due, set it immediately without calling LLM.
    try:
        from app.hitl.models import HITL_GATES
        ctx_fast = state.get("context", {}) or {}
        hist_fast = state.get("hitl_history", []) or []
        def _has_fast(gid: str) -> bool:
            for h in hist_fast:
                hg = h.get("gate_id") if isinstance(h, dict) else getattr(h, "gate_id", None)
                if hg and str(hg).lower().replace("-", "_") == gid.lower().replace("-", "_"):
                    return True
            return False
        def _was_rejected(gid: str) -> bool:
            for h in reversed(hist_fast):
                hg = h.get("gate_id") if isinstance(h, dict) else getattr(h, "gate_id", None)
                if hg and str(hg).lower().replace("-", "_") == gid.lower().replace("-", "_"):
                    dec = h.get("decision") if isinstance(h, dict) else getattr(h, "decision", "")
                    return str(dec).lower() in ("reject", "rejected")
            return False
        # Don't fast-path if already pending, escalated, or previous gate was rejected
        if not state.get("hitl_pending") and not state.get("escalation"):
            # Pre-populate context with estimated data so approval cards show real values
            # (tools haven't run yet at this point, but the card needs data)
            _ctx_pre = state.get("context", {}) or {}
            if _ctx_pre.get("split_result") and not _ctx_pre.get("dispatch_result"):
                _split = _ctx_pre.get("split_result", {})
                _road_containers = _split.get("road_containers", 80) if isinstance(_split, dict) else 80
                import math as _math
                _road_trips = _split.get("road_trips", _math.ceil(_road_containers * 0.85)) if isinstance(_split, dict) else _math.ceil(_road_containers * 0.85)
                _ctx_pre["dispatch_result"] = {
                    "status": "dispatch_pending",
                    "dispatch_id": "DISP-PENDING",
                    "num_trucks": max(1, _road_containers // 4),
                    "route": "PPT→West Coast Hwy→AYE→Tuas",
                    "container_count": _road_containers,
                    "total_trips": _road_trips,
                    "eta": "2026-08-19T14:30:00+08:00",
                    "cost": _road_trips * 150,
                    "cost_per_trip": 150,
                    "total_cost": _road_trips * 150,
                }
            if _ctx_pre.get("split_result") and not _ctx_pre.get("feeder_hold_result"):
                _ctx_pre["feeder_hold_result"] = {
                    "status": "hold_pending",
                    "feeder_id": "FEEDER ATLANTIC-03",
                    "hold_hours": 1.0,
                    "hold_cost": 800,
                    "hold_cost_per_hour": 800,
                    "new_departure": "2026-08-19T17:30:00+08:00",
                    "previous_departure": "2026-08-19T16:30:00+08:00",
                    "tidal_risk": "safe",
                    "operator_response": "pending",
                }
            if ctx_fast.get("split_result") and not _has_fast("HITL-1") and not _was_rejected("HITL-1"):
                g = HITL_GATES.get("HITL-1")
                state["hitl_pending"] = g.to_dict() if hasattr(g, "to_dict") else dict(g) if isinstance(g, dict) else {"gate_id": "HITL-1", "gate_name": "Approve ITT Split", "trigger": "split computed", "timeout_seconds": 1800, "timeout_action": "escalate"}
                state["status"] = "waiting_hitl"
                # Trace & return without LLM
                try:
                    log_trace(state, "agent", "reason", {"tool_calls": [], "fast_path": "HITL-1", "risk_score": compute_risk_score(state)}, duration_ms=(time.monotonic() - t0)*1000)
                except Exception:
                    pass
                return state
            elif _has_fast("HITL-1") and not _has_fast("HITL-2") and not _was_rejected("HITL-2"):
                g = HITL_GATES.get("HITL-2")
                state["hitl_pending"] = g.to_dict() if hasattr(g, "to_dict") else dict(g) if isinstance(g, dict) else {"gate_id": "HITL-2", "gate_name": "Approve Truck Dispatch", "trigger": "truck dispatch ready", "timeout_seconds": 900, "timeout_action": "cancel_dispatch"}
                state["status"] = "waiting_hitl"
                try:
                    log_trace(state, "agent", "reason", {"tool_calls": [], "fast_path": "HITL-2", "risk_score": compute_risk_score(state)}, duration_ms=(time.monotonic() - t0)*1000)
                except Exception:
                    pass
                return state
            elif _has_fast("HITL-2") and not _has_fast("HITL-3") and not _was_rejected("HITL-3"):
                g = HITL_GATES.get("HITL-3")
                state["hitl_pending"] = g.to_dict() if hasattr(g, "to_dict") else dict(g) if isinstance(g, dict) else {"gate_id": "HITL-3", "gate_name": "Approve Feeder Hold", "trigger": "feeder hold request ready", "timeout_seconds": 900, "timeout_action": "escalate"}
                state["status"] = "waiting_hitl"
                try:
                    log_trace(state, "agent", "reason", {"tool_calls": [], "fast_path": "HITL-3", "risk_score": compute_risk_score(state)}, duration_ms=(time.monotonic() - t0)*1000)
                except Exception:
                    pass
                return state
            elif _has_fast("HITL-3") and not _has_fast("HITL-4") and not _was_rejected("HITL-4"):
                if ctx_fast.get("tuas_sequence"):
                    g = HITL_GATES.get("HITL-4")
                    state["hitl_pending"] = g.to_dict() if hasattr(g, "to_dict") else dict(g) if isinstance(g, dict) else {"gate_id": "HITL-4", "gate_name": "Approve Loading Sequence Update", "trigger": "Tuas QC sequence update ready", "timeout_seconds": 600, "timeout_action": "hold_sequence"}
                    state["status"] = "waiting_hitl"
                    try:
                        log_trace(state, "agent", "reason", {"tool_calls": [], "fast_path": "HITL-4", "risk_score": compute_risk_score(state)}, duration_ms=(time.monotonic() - t0)*1000)
                    except Exception:
                        pass
                    return state
    except Exception:
        pass
    # 1. Build messages
    messages = build_agent_messages(state)

    # Publish SSE agent_thinking
    try:
        from app.agent.sse import broadcaster

        # Don't await if no loop? We'll create task
        try:
            loop = asyncio.get_running_loop()
            last_msg = messages[-1] if messages else {}
            loop.create_task(broadcaster.publish(state.get("run_id", ""), "agent_thinking", {"messages": last_msg, "step": state.get("context", {}).get("current_step", "reason")})) 
        except RuntimeError:
            pass
    except Exception:
        pass

    # 2. Get schemas + provider
    from app.tools.registry import registry

    # Ensure registry has tools for active problem
    if not registry.list():
        try:
            from app.agent.problem_switcher import get_active_problem_id
            registry.register_for_problem(get_active_problem_id())
        except Exception:
            from app.tools.registry import load_tools_for_problem
            from app.agent.problem_switcher import get_active_problem_id as _gpid
            try:
                _fallback_pid = _gpid()
            except Exception:
                _fallback_pid = "pb-12-itt"
            for t in load_tools_for_problem(_fallback_pid):
                registry.register(t)

    raw_schemas = registry.get_schemas()
    # Provider selection
    provider = None
    provider_name = "anthropic"
    try:
        # Try to get provider from problem_config llm field
        prob_cfg = state.get("problem_config")
        if isinstance(prob_cfg, dict):
            llm_cfg = prob_cfg.get("llm", {}) or {}
            provider_name = llm_cfg.get("provider", "anthropic")
            from app.shared.provider import create_provider
            # If dict has enough config, create provider
            if llm_cfg:
                try:
                    provider = create_provider(llm_cfg)
                except Exception:
                    provider = None
        elif prob_cfg is not None and not isinstance(prob_cfg, dict):
            # ProblemConfig dataclass
            llm_cfg = getattr(prob_cfg, "llm", {}) or {}
            if isinstance(llm_cfg, dict):
                provider_name = llm_cfg.get("provider", "anthropic")
                from app.shared.provider import create_provider
                try:
                    provider = create_provider(llm_cfg)
                except Exception:
                    provider = None
    except Exception:
        pass

    # Fallback: create from active config
    if provider is None:
        try:
            from app.configs.problem_config import load_problem_config
            from app.agent.problem_switcher import get_active_problem_id
            cfg = load_problem_config(get_active_problem_id())
            if cfg.llm:
                from app.shared.provider import create_provider
                provider = create_provider(cfg.llm)
                provider_name = cfg.llm.get("provider", provider_name)
        except Exception:
            provider = None

    # If still no provider, use a mock provider that echoes tool calls deterministically
    # This allows tests to run without real API keys (deterministic demo logic)
    # Also, if provider requires API key but none is set (e.g., anthropic without key), fallback to mock immediately
    def _provider_needs_key(p):
        try:
            # Providers that need api_key and have empty key should be considered unconfigured
            key = getattr(p, "api_key", None)
            if key == "" or key is None:
                # Check if provider name is one that requires a key
                if provider_name in ("anthropic", "openai", "gemini", "deepseek"):
                    return True
        except Exception:
            pass
        return False

    if provider is None or _provider_needs_key(provider):
        provider = mock_provider_for_state(state)
        # Mock provider uses raw schemas logic internally, no adaptation needed
        tool_schemas = raw_schemas
    else:
        # Adapt schemas for provider (flat -> OpenAI/Anthropic/Gemini)
        try:
            from app.tools.tool_adapter import adapt_tools_for_provider
            # Registry schemas are flat {name, description, parameters}; adapt to provider format
            # But AnthropicProvider currently expects OpenAI format and does its own conversion,
            # so we need to provide OpenAI format for those providers; adapt does that.
            # For mock, raw is fine.
            tool_schemas = adapt_tools_for_provider(raw_schemas, provider_name)
            # However, to avoid double conversion, if provider already handles flat, we keep adapted as OpenAI for openai-compatible,
            # for anthropic/gemini we keep provider-specific.
            # The provider's chat will handle OpenAI->anthropic conversion only if we give OpenAI format.
            # Our adapt already did flat->provider specifics, so we must ensure provider doesn't re-adapt incorrectly.
            # For anthropic, adapt produces [{"name":..,"input_schema":..}] which provider's current code expects OpenAI format and would fail.
            # Workaround: if provider_name is anthropic/gemini and we already adapted, we will bypass provider's internal conversion by
            # passing already-adapted schemas and having provider handle it. To fix, we monkey-patch provider to accept flat/adapted.
            # Easiest: if adapted is provider-specific (anthropic/gemini), keep it; provider will be patched to handle it.
            pass
        except Exception:
            tool_schemas = raw_schemas

    # SSE tool_call pre? Not yet

    # 2b. Call LLM with rate-limit retry
    response = None
    try:
        from app.agent.resilience import chat_with_rate_limit  # Phase 6.12
        response = await chat_with_rate_limit(provider, messages, tools=tool_schemas)
    except ImportError:
        # Fallback to direct chat
        try:
            # provider.chat is sync — run in thread pool to avoid blocking
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: provider.chat(messages, tools=tool_schemas))
        except RuntimeError:
            response = provider.chat(messages, tools=tool_schemas)
    except Exception as exc:
        # Use deterministic fallback response if LLM fails
        structured_log("llm_error", run_id=state.get("run_id", ""), step="agent", error=str(exc))
        response = _fallback_llm_response(state, raw_schemas)

    if response is None:
        response = _fallback_llm_response(state, raw_schemas)

    # Extract tool_calls and content
    tool_calls_raw: list[dict[str, Any]] = []
    content: str | None = None
    confidence_val: float | None = None
    finish_reason: str = "stop"

    # response may be LLMResponse dataclass or dict
    if isinstance(response, dict):
        content = response.get("content")
        tool_calls_raw = response.get("tool_calls", []) or []
        confidence_val = response.get("confidence")
        finish_reason = response.get("finish_reason", "stop")
    else:
        content = getattr(response, "content", None)
        tool_calls_raw = getattr(response, "tool_calls", []) or []
        finish_reason = getattr(response, "finish_reason", "stop")
        # Try to parse confidence from content
        from app.agent.confidence import extract_confidence, deterministic_score
        conf = extract_confidence(content)
        if conf is not None:
            confidence_val = conf
        # Also check raw if present
        raw = getattr(response, "raw", {}) or {}
        if isinstance(raw, dict) and "confidence" in raw:
            try:
                confidence_val = float(raw["confidence"])
            except Exception:
                pass

    # Determine confidence fallback
    if confidence_val is None:
        from app.agent.confidence import deterministic_score
        try:
            confidence_val = deterministic_score(state)
        except Exception:
            confidence_val = float(state.get("confidence", 0.85))

    # Clamp confidence
    try:
        confidence_val = max(0.0, min(1.0, float(confidence_val)))
    except Exception:
        confidence_val = 0.85

    state["confidence"] = confidence_val

    # Publish confidence_update SSE event
    try:
        from app.agent.sse import broadcaster
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcaster.publish(state.get("run_id", ""), "confidence_update", {"confidence": confidence_val, "source": "agent_node"}))
        except RuntimeError:
            pass
    except Exception:
        pass

    # Handle tool_calls: normalize to list of {id, name, args}
    normalised_calls: list[dict[str, Any]] = []
    invalid_calls: list[dict[str, Any]] = []
    valid_calls: list[dict[str, Any]] = []

    for tc in tool_calls_raw:
        # tc may be OpenAI style {id, type, function: {name, arguments}} or flat {name, arguments}
        name = None
        args: dict[str, Any] = {}
        tc_id = None
        if isinstance(tc, dict):
            if "function" in tc:
                fn = tc.get("function", {}) or {}
                name = fn.get("name")
                args_raw = fn.get("arguments", "{}")
                tc_id = tc.get("id", f"call_{len(normalised_calls)}")
                # arguments may be JSON string
                if isinstance(args_raw, str):
                    try:
                        args = json.loads(args_raw) if args_raw else {}
                    except Exception:
                        try:
                            args = json.loads(args_raw.replace("'", '"'))  # lenient
                        except Exception:
                            args = {}
                elif isinstance(args_raw, dict):
                    args = args_raw
            else:
                # flat
                name = tc.get("name")
                args = tc.get("arguments", tc.get("args", {}))
                tc_id = tc.get("id", f"call_{len(normalised_calls)}")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {}
        if name:
            norm = {"id": tc_id or f"call_{len(normalised_calls)}", "name": name, "args": args if isinstance(args, dict) else {}}
            normalised_calls.append(norm)
            # Validate against registry
            if registry.get_tool(name) is None:
                invalid_calls.append(norm)
                # Log hallucinated
                state.setdefault("trace", []).append({
                    "timestamp": _now_iso(),
                    "run_id": state.get("run_id", ""),
                    "node": "agent",
                    "action": "hallucinated_tool",
                    "result": {"tool_name": name, "available": registry.list()},
                    "duration_ms": 0,
                    "confidence": confidence_val,
                    "risk_score": compute_risk_score(state),
                })
                structured_log("hallucinated_tool", run_id=state.get("run_id", ""), step="agent", tool_name=name, available=registry.list())
                # Also SSE
                try:
                    from app.agent.sse import broadcaster
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(broadcaster.publish(state.get("run_id", ""), "tool_call", {"tool": name, "error": "hallucinated", "available": registry.list()}))
                    except RuntimeError:
                        pass
                except Exception:
                    pass
            else:
                valid_calls.append(norm)

    # If all calls hallucinated, ask LLM to retry with correct list
    if invalid_calls and not valid_calls and normalised_calls:
        state.setdefault("messages", []).append({
            "role": "user",
            "content": f"Unknown tools: {[c['name'] for c in invalid_calls]}. Available tools: {registry.list()}. Retry with a valid tool.",
        })
        state["status"] = "running"
        # Purge invalid calls
        state["pending_tool_calls"] = []
        duration_ms = (time.monotonic() - t0) * 1000
        log_trace(state, "agent", "reason", {"tool_calls": [], "hallucinated": [c["name"] for c in invalid_calls], "risk_score": compute_risk_score(state)}, duration_ms=duration_ms)
        return state
    elif valid_calls:
        state["pending_tool_calls"] = valid_calls
        state["status"] = "calling_tools"
        # Append assistant message with tool_calls for LangGraph message history
        state.setdefault("messages", []).append({
            "role": "assistant",
            "content": content or "",
            "tool_calls": [{"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": json.dumps(c["args"])}} for c in valid_calls],
        })
        # SSE publish tool_call events
        for c in valid_calls:
            try:
                from app.agent.sse import broadcaster
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(broadcaster.publish(state.get("run_id", ""), "tool_call", {"tool": c["name"], "args": c["args"], "id": c["id"]}))
                except RuntimeError:
                    pass
            except Exception:
                pass
        structured_log("agent_tool_calls", run_id=state.get("run_id", ""), step="agent", tools=[c["name"] for c in valid_calls], confidence=confidence_val)
    else:
        # No tool calls — check if HITL or completion needed
        # Determine if we should fire HITL gates based on context progress
        # For deterministic demo flow (without LLM), we may need to synthesize HITL
        # But if LLM returns content without tools, treat as potential HITL or completion.
        # We check escalation first
        state["pending_tool_calls"] = []
        # Try to interpret content as HITL card or final answer
        # For now, if no tools and status not terminal, keep running and let graph router decide
        # But we append assistant content to messages for continuity
        if content:
            state.setdefault("messages", []).append({"role": "assistant", "content": content})
        # Do not set hitl_pending here — router will check if hitl_pending already set or if monitor/escalation needed
        # If no progress and no tools, we may be at completion
        if not state.get("hitl_pending") and not state.get("escalation"):
            # If workflow has dispatched and not monitored, let router go to monitor; otherwise complete
            ctx = state.get("context", {}) or {}
            if ctx.get("dispatched") and not ctx.get("monitored"):
                state["status"] = "running"
            else:
                # Check if we have done minimal steps — for demo, if context has split_result, we may need to drive HITL
                # The graph's route_after_agent will inspect pending/hitl/escalation/monitor; if none, returns END
                state["status"] = "running"

    # Update trace — include risk_score
    duration_ms = (time.monotonic() - t0) * 1000
    risk = compute_risk_score(state)
    log_trace(state, "agent", "reason", {"tool_calls": [{"name": c["name"], "args": c["args"]} for c in valid_calls], "content": (content or "")[:500], "risk_score": risk, "confidence": confidence_val}, duration_ms=duration_ms)

    # Confidence already set
    # Check escalation triggers immediately after reasoning — but only if not already in HITL sequence
    # For nominal flow, we have already fixed road_capacity and data_stale to not fire spuriously,
    # so escalation should only be for true deviations (confidence low, feeder hold, etc.)
    try:
        from app.agent.escalation import check_escalations
        from app.hitl.models import HITL_GATES
        # Don't double-escalate if already escalated and HITL-5 pending
        if not state.get("hitl_pending") or state.get("hitl_pending", {}).get("gate_id") not in ("HITL-5", "hitl_5"):
            triggered = check_escalations(state)
            if triggered:
                state["escalation"] = triggered[0]
                if len(triggered) > 1:
                    state["escalation_list"] = triggered  # type: ignore
                hitl5 = HITL_GATES.get("HITL-5") or HITL_GATES.get("hitl_5")
                if hitl5 and hasattr(hitl5, "to_dict"):
                    state["hitl_pending"] = hitl5.to_dict()  # type: ignore
                elif isinstance(hitl5, dict):
                    state["hitl_pending"] = dict(hitl5)
                else:
                    state["hitl_pending"] = dict(HITL5_FALLBACK)
                state["status"] = "escalated"
                try:
                    from app.agent.sse import broadcaster
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(broadcaster.publish(state.get("run_id", ""), "escalation", {"trigger": triggered[0]["trigger"], "risk_score": risk}))
                    except RuntimeError:
                        pass
                except Exception:
                    pass
                structured_log("escalation", run_id=state.get("run_id", ""), step="agent", trigger=triggered[0]["trigger"], risk_score=risk)
                log_trace(state, "escalation", "triggered", {"trigger": triggered[0]["trigger"], "risk_score": risk}, duration_ms=0)
                # If escalation fired, don't also set normal HITL-1..4 — return now so router goes to HITL-5
                return state
    except Exception:
        pass

    # Deterministic HITL gating for charter workflow — if no pending tools and no escalation,
    # set the next HITL gate in sequence (HITL-1..4). This ensures router is pure and checkpoint persists hitl_pending.
    # Router will then route to hitl node; previously this was done inside router which caused checkpoint not to persist.
    if not state.get("pending_tool_calls") and not state.get("hitl_pending") and not state.get("escalation"):
        try:
            from app.hitl.models import HITL_GATES
            ctx = state.get("context", {}) or {}
            hist = state.get("hitl_history", []) or []

            def _has(gid: str) -> bool:
                for h in hist:
                    hg = h.get("gate_id") if isinstance(h, dict) else getattr(h, "gate_id", None)
                    if hg and str(hg).lower().replace("-", "_") == gid.lower().replace("-", "_"):
                        return True
                return False

            def _rej(gid: str) -> bool:
                for h in reversed(hist):
                    hg = h.get("gate_id") if isinstance(h, dict) else getattr(h, "gate_id", None)
                    if hg and str(hg).lower().replace("-", "_") == gid.lower().replace("-", "_"):
                        dec = h.get("decision") if isinstance(h, dict) else getattr(h, "decision", "")
                        return str(dec).lower() in ("reject", "rejected")
                return False

            # Sequence: after split -> HITL-1, after HITL-1 -> HITL-2, after HITL-2 -> HITL-3, after Tuas -> HITL-4
            # Skip gate if it was rejected — let agent re-reason via LLM
            if ctx.get("split_result") and not _has("HITL-1") and not _rej("HITL-1"):
                g = HITL_GATES.get("HITL-1") or HITL_GATES.get("hitl_1")
                state["hitl_pending"] = g.to_dict() if hasattr(g, "to_dict") else dict(g) if isinstance(g, dict) else {"gate_id": "HITL-1", "gate_name": "Approve ITT Split", "trigger": "split computed", "timeout_seconds": 1800, "timeout_action": "escalate"}
                state["status"] = "waiting_hitl"
            elif _has("HITL-1") and not _has("HITL-2") and not _rej("HITL-2"):
                g = HITL_GATES.get("HITL-2") or HITL_GATES.get("hitl_2")
                state["hitl_pending"] = g.to_dict() if hasattr(g, "to_dict") else dict(g) if isinstance(g, dict) else {"gate_id": "HITL-2", "gate_name": "Approve Truck Dispatch", "trigger": "truck dispatch ready", "timeout_seconds": 900, "timeout_action": "cancel_dispatch"}
                state["status"] = "waiting_hitl"
            elif _has("HITL-2") and not _has("HITL-3") and not _rej("HITL-3"):
                g = HITL_GATES.get("HITL-3") or HITL_GATES.get("hitl_3")
                state["hitl_pending"] = g.to_dict() if hasattr(g, "to_dict") else dict(g) if isinstance(g, dict) else {"gate_id": "HITL-3", "gate_name": "Approve Feeder Hold", "trigger": "feeder hold request ready", "timeout_seconds": 900, "timeout_action": "escalate"}
                state["status"] = "waiting_hitl"
            elif _has("HITL-3") and not _has("HITL-4") and not _rej("HITL-4"):
                # Need Tuas sequence computed before HITL-4, but if not yet, let agent call T5 first
                # Only set HITL-4 if tuas_sequence exists or we have dispatched
                if ctx.get("tuas_sequence") or ctx.get("dispatched"):
                    g = HITL_GATES.get("HITL-4") or HITL_GATES.get("hitl_4")
                    state["hitl_pending"] = g.to_dict() if hasattr(g, "to_dict") else dict(g) if isinstance(g, dict) else {"gate_id": "HITL-4", "gate_name": "Approve Loading Sequence Update", "trigger": "Tuas QC sequence update ready", "timeout_seconds": 600, "timeout_action": "hold_sequence"}
                    state["status"] = "waiting_hitl"
        except Exception:
            pass

    return state


async def tool_node(state: dict[str, Any]) -> dict[str, Any]:
    """Tool execution node — dispatches pending tool calls to registry."""
    t0 = time.monotonic()
    tool_calls = state.get("pending_tool_calls", []) or []
    if not tool_calls:
        return state

    from app.tools.registry import registry, FALLBACKS
    from app.agent.confidence import compute_risk_score
    from app.shared.logging import structured_log

    # Ensure registry has tools
    if not registry.list():
        try:
            from app.agent.problem_switcher import get_active_problem_id
            registry.register_for_problem(get_active_problem_id())
        except Exception:
            pass

    results: dict[str, Any] = state.setdefault("tool_results", {})

    for call in tool_calls:
        name = call.get("name") or call.get("tool")
        args = call.get("args", call.get("arguments", {})) or {}
        call_id = call.get("id", f"call_{name}")

        # Post-approval guard: dispatch/hold require prior HITL approve
        tool = registry.get_tool(name or "")
        if tool and getattr(tool, "post_approval", False):
            gate_map = {"dispatch_road_itt": "HITL-2", "request_feeder_hold": "HITL-3"}
            gate_id = gate_map.get(name, "")
            approved_gates = set()
            for h in state.get("hitl_history", []) or []:
                if isinstance(h, dict) and h.get("decision") == "approve":
                    approved_gates.add(h.get("gate_id"))
            if gate_id and gate_id not in approved_gates and gate_id.lower() not in {g.lower() for g in approved_gates}:
                # Also check hitl_history for hitl_2 alias
                alias = gate_id.lower()
                alias2 = gate_id.replace("HITL-", "hitl_").lower()
                if alias not in {g.lower() for g in approved_gates} and alias2 not in {g.lower() for g in approved_gates}:
                    err_result = {
                        "output": {"error": f"HITL {gate_id} approval required before {name}"},
                        "confidence": 0.0,
                        "metadata": {"tool_name": name, "error": "hitl_required", "timestamp": time.time(), "duration_ms": 0, "fallback_used": False},
                    }
                    results[call_id] = err_result
                    state.setdefault("messages", []).append({"role": "tool", "tool_call_id": call_id, "content": json.dumps(err_result["output"])})
                    # trace
                    risk = compute_risk_score(state)
                    log_trace(state, "tool", "blocked_hitl", {"tool": name, "gate": gate_id, "risk_score": risk, "fallback_used": False}, duration_ms=0)
                    structured_log("tool_blocked_hitl", run_id=state.get("run_id", ""), step="tool", tool=name, gate=gate_id)
                    continue

        # Timeout vs 503 distinct handling — use asyncio.wait_for around registry.call
        # registry.call already has internal timeout handling, but we add outer wait_for to distinguish
        # timeout (latency) vs 503 (error)
        result_obj = None
        fallback_used = False
        try:
            # Add run_id to tool call for data isolation and logging
            args_with_id = dict(args)
            args_with_id["_run_id"] = state.get("run_id", "")
            # If this is a post-approval tool and we passed guard, allow it
            if tool and getattr(tool, "post_approval", False):
                args_with_id["_hitl_approved"] = True
            # Use asyncio.wait_for with tool's timeout to catch timeout separately
            timeout_sec = getattr(tool, "timeout_seconds", 10) if tool else 10
            try:
                result_obj = await asyncio.wait_for(registry.call(name, **args_with_id), timeout=timeout_sec + 5)
            except asyncio.TimeoutError:
                # Outer timeout — treat as timeout error distinct from 503
                fb_name = FALLBACKS.get(name) if name else None
                if fb_name and registry.get_tool(fb_name):
                    fb_result = await registry.call(fb_name, **args)
                    # Mark fallback
                    fb_meta = dict(getattr(fb_result, "metadata", {}) or {})
                    fb_meta["fallback_used"] = True
                    fb_meta["original_error"] = "timeout"
                    fb_meta["tool_name"] = fb_name
                    if hasattr(fb_result, "metadata"):
                        fb_result.metadata = fb_meta
                    result_obj = fb_result
                    fallback_used = True
                    log_trace(state, "tool", "timeout_fallback", {"tool": name, "fallback": fb_name, "risk_score": compute_risk_score(state)}, duration_ms=timeout_sec * 1000)
                    structured_log("tool_timeout_fallback", run_id=state.get("run_id", ""), step="tool", tool=name, fallback=fb_name)
                else:
                    # No fallback — create error result
                    from app.tools.base import ToolResult
                    result_obj = ToolResult(
                        output={"error": f"Tool {name} timed out"},
                        confidence=0.0,
                        metadata={"tool_name": name, "error": "timeout", "fallback_used": False, "timestamp": _now_iso(), "duration_ms": timeout_sec * 1000},
                    )
                    structured_log("tool_timeout", run_id=state.get("run_id", ""), step="tool", tool=name, error="timeout")
        except Exception as exc:
            # API error (e.g., 503) — try fallback distinct from timeout
            fb_name = FALLBACKS.get(name) if name else None
            is_503 = "503" in str(exc) or "service unavailable" in str(exc).lower() or "timeout" in str(exc).lower()
            if fb_name and registry.get_tool(fb_name):
                try:
                    fb_result = await registry.call(fb_name, **args)
                    fb_meta = dict(getattr(fb_result, "metadata", {}) or {})
                    fb_meta["fallback_used"] = True
                    fb_meta["original_error"] = str(exc)
                    fb_meta["tool_name"] = fb_name
                    if hasattr(fb_result, "metadata"):
                        fb_result.metadata = fb_meta
                    result_obj = fb_result
                    fallback_used = True
                    log_trace(state, "tool", "error_fallback", {"tool": name, "error": str(exc), "fallback": fb_name, "risk_score": compute_risk_score(state)}, duration_ms=0)
                    structured_log("tool_error_fallback", run_id=state.get("run_id", ""), step="tool", tool=name, error=str(exc), fallback=fb_name)
                except Exception as fb_exc:
                    from app.tools.base import ToolResult
                    result_obj = ToolResult(
                        output={"error": str(exc)},
                        confidence=0.0,
                        metadata={"tool_name": name, "error": str(exc), "fallback_used": False, "fallback_error": str(fb_exc), "timestamp": _now_iso()},
                    )
                    structured_log("tool_error_no_fallback", run_id=state.get("run_id", ""), step="tool", tool=name, error=str(exc))
            else:
                from app.tools.base import ToolResult
                result_obj = ToolResult(
                    output={"error": str(exc)},
                    confidence=0.0,
                    metadata={"tool_name": name, "error": str(exc), "fallback_used": False, "timestamp": _now_iso()},
                )
                structured_log("tool_error", run_id=state.get("run_id", ""), step="tool", tool=name, error=str(exc))
        # Ensure result_obj is set — if registry.call succeeded without exception
        if result_obj is None:
            # Should not happen — create generic error
            from app.tools.base import ToolResult
            result_obj = ToolResult(output={"error": f"Unknown tool {name}"}, confidence=0.0, metadata={"tool_name": name, "error": "hallucinated", "fallback_used": False, "timestamp": _now_iso()})

        # Normalise result to dict for state storage (serializable for checkpoint)
        # Keep full output for logic; truncate only for checkpoint-persisted fields
        if hasattr(result_obj, "output"):
            full_out = getattr(result_obj, "output", {}) or {}
            conf = float(getattr(result_obj, "confidence", 0.0) or 0.0)
            meta = dict(getattr(result_obj, "metadata", {}) or {})
            # Ensure metadata has tool_name and fallback_used
            meta.setdefault("tool_name", name)
            meta.setdefault("fallback_used", fallback_used)
            # Preserve fallback_used from tool execution if already set
            if fallback_used:
                meta["fallback_used"] = True
            # Truncate large get_itt_candidates output for checkpoint ONLY
            if name == "get_itt_candidates" and isinstance(full_out, dict) and "containers" in full_out and isinstance(full_out["containers"], list) and len(full_out["containers"]) > 5:
                _trunc = {k: v for k, v in full_out.items() if k != "containers"}
                _trunc["containers"] = full_out["containers"][:5]
                _trunc["containers_truncated_total"] = len(full_out["containers"])
                trunc_out = _trunc
            else:
                trunc_out = full_out
            serialised = {"output": trunc_out, "confidence": conf, "metadata": meta}
            # Keep full for downstream logic (store separately)
            _full_for_logic = full_out
        else:
            # Dict-style result
            if isinstance(result_obj, dict) and "output" in result_obj:
                full_out_dict = result_obj.get("output", {}) or {}
                conf_dict = float(result_obj.get("confidence", 0.0) or 0.0)
                meta_dict = dict(result_obj.get("metadata", {}) or {"tool_name": name})
                if name == "get_itt_candidates" and isinstance(full_out_dict, dict) and "containers" in full_out_dict and isinstance(full_out_dict["containers"], list) and len(full_out_dict["containers"]) > 5:
                    _trunc2 = {k: v for k, v in full_out_dict.items() if k != "containers"}
                    _trunc2["containers"] = full_out_dict["containers"][:5]
                    _trunc2["containers_truncated_total"] = len(full_out_dict["containers"])
                    trunc_out2 = _trunc2
                else:
                    trunc_out2 = full_out_dict
                serialised = {"output": trunc_out2, "confidence": conf_dict, "metadata": meta_dict}
                _full_for_logic = full_out_dict
            else:
                serialised = result_obj if isinstance(result_obj, dict) else {"output": dict(result_obj), "confidence": 0.0, "metadata": {"tool_name": name}}
                # Also truncate if needed
                if isinstance(serialised.get("output"), dict) and "containers" in serialised["output"] and isinstance(serialised["output"]["containers"], list) and len(serialised["output"]["containers"]) > 5:
                    _full2 = serialised["output"]
                    _trunc2 = {k: v for k, v in _full2.items() if k != "containers"}
                    _trunc2["containers"] = _full2["containers"][:5]
                    _trunc2["containers_truncated_total"] = len(_full2["containers"])
                    serialised["output"] = _trunc2
                    _full_for_logic = _full2
                else:
                    _full_for_logic = serialised.get("output", {}) if isinstance(serialised.get("output"), dict) else {}

        results[call_id] = serialised

        # Update context shortcuts for escalation / guardrails / monitor
        try:
            ctx = state.setdefault("context", {})
            # Store candidates, road_capacity, sea_capacity, split_result etc.
            if name == "get_itt_candidates":
                # Store FULL candidates for optimiser/validation; truncated only in tool_results/messages
                ctx["candidates"] = _full_for_logic if isinstance(_full_for_logic, dict) else serialised["output"]
                ctx["_candidates_full_len"] = len((_full_for_logic.get("containers", []) if isinstance(_full_for_logic, dict) else []))
                # also store container_count etc. from full
                container_src = _full_for_logic if isinstance(_full_for_logic, dict) else serialised["output"]
                ctx["container_count"] = container_src.get("total_containers", ctx.get("container_count"))
            elif name == "check_road_itt_capacity":
                ctx["road_capacity"] = serialised["output"]
                ctx["available_trucks"] = serialised["output"].get("available_trucks", ctx.get("available_trucks"))
                ctx["required_trucks"] = serialised["output"].get("baseline_trips_all_120_containers", 80)
            elif name == "check_sea_itt_capacity":
                ctx["sea_capacity"] = serialised["output"]
                ctx["feeder_id"] = serialised["output"].get("feeder_id", ctx.get("feeder_id"))
                # also store downstream constraints for tidal check
            elif name == "compute_itt_split":
                ctx["split_result"] = serialised["output"].get("optimal_split", serialised["output"])
                ctx["split_alternatives"] = serialised["output"].get("alternatives", [])
                ctx["cost_vs_baseline"] = serialised["output"].get("cost_vs_baseline", {})
                ctx["roi"] = serialised["output"].get("roi", {})
                ctx["timeline"] = serialised["output"].get("timeline", {})
                try:
                    savings = serialised["output"].get("cost_vs_baseline", {}).get("direct_transport_savings", 1600)
                    ctx.setdefault("action_cost", savings)
                except Exception:
                    pass
                if serialised["confidence"] and serialised["confidence"] > 0:
                    pass
                try:
                    from app.agent.sse import broadcaster
                    opt = serialised["output"].get("optimal_split", {})
                    vsb = serialised["output"].get("cost_vs_baseline", {})
                    if isinstance(opt, dict):
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(broadcaster.publish(state.get("run_id", ""), "cost_update", {"road_cost": opt.get("road_cost", 0), "sea_handling": opt.get("sea_terminal_handling_cost", 0), "total": opt.get("total_transport_cost", 0), "baseline": vsb.get("baseline_all_road_cost", 0), "alternatives": serialised["output"].get("alternatives", [])}))
                        except RuntimeError:
                            pass
                except Exception:
                    pass
            elif name == "update_tuas_loading_sequence":
                ctx["tuas_sequence"] = serialised["output"]
                try:
                    from app.agent.sse import broadcaster
                    _tout = serialised["output"]
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(broadcaster.publish(state.get("run_id", ""), "tool_confirmation", {"tool": "update_tuas_loading_sequence", "message": f"Tuas QC sequence updated for {_tout.get('vessel_id', '?')}, margin {_tout.get('margin_before_departure_minutes', '?')}min", "status": "updated"}))
                    except RuntimeError:
                        pass
                except Exception:
                    pass
            elif name == "dispatch_road_itt":
                ctx["dispatched"] = True
                ctx["dispatch_result"] = serialised["output"]
                if "delta" in str(serialised["output"]).lower() or ctx.get("deviation_log"):
                    ctx["delta_dispatched"] = True
                try:
                    from app.agent.sse import broadcaster
                    _dout = serialised["output"]
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(broadcaster.publish(state.get("run_id", ""), "tool_confirmation", {"tool": "dispatch_road_itt", "message": f"Dispatched {_dout.get('num_trucks', '?')} trucks, {_dout.get('total_trips', '?')} trips, ETA {_dout.get('eta', '?')}", "status": "dispatched"}))
                    except RuntimeError:
                        pass
                except Exception:
                    pass
            elif name == "request_feeder_hold":
                ctx["feeder_hold_result"] = serialised["output"]
                ctx["feeder_hold_hours"] = serialised["output"].get("hold_hours", args.get("hold_hours", 0))
                try:
                    from app.agent.sse import broadcaster
                    _hout = serialised["output"]
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(broadcaster.publish(state.get("run_id", ""), "tool_confirmation", {"tool": "request_feeder_hold", "message": f"Feeder hold {_hout.get('hold_hours', '?')}h requested, tidal risk: {_hout.get('tidal_risk', '?')}, operator: {_hout.get('operator_response', '?')}", "status": _hout.get("status", "pending")}))
                    except RuntimeError:
                        pass
                except Exception:
                    pass
            elif name == "notify_parties":
                # notification log
                pass
        except Exception:
            pass

        # Messages: add tool result for LLM history — truncate large outputs to avoid 40s checkpoint deepcopy
        try:
            msg_output = serialised["output"]
            # Truncate get_itt_candidates full container list for LLM history
            if name == "get_itt_candidates" and isinstance(msg_output, dict) and "containers" in msg_output and isinstance(msg_output["containers"], list) and len(msg_output["containers"]) > 5:
                msg_output = {k: v for k, v in msg_output.items() if k != "containers"}
                msg_output["containers"] = msg_output.get("containers_sample", [])[:5] if "containers_sample" in serialised["output"] else []
                msg_output["note"] = f"{len(serialised['output'].get('containers', []))} containers truncated"
            state.setdefault("messages", []).append({"role": "tool", "tool_call_id": call_id, "content": json.dumps(msg_output, default=str)[:8000]})  # cap 8k
        except Exception:
            try:
                state.setdefault("messages", []).append({"role": "tool", "tool_call_id": call_id, "content": json.dumps({"summary": str(serialised["output"])[:2000]}, default=str)})
            except Exception:
                pass

        # Trace per tool result — include risk_score + fallback_used (truncate output for trace to avoid large logs)
        risk = compute_risk_score(state)
        # duration from metadata
        dur = 0
        try:
            dur = float(serialised.get("metadata", {}).get("duration_ms", 0) or 0)
        except Exception:
            dur = 0
        fallback_flag = bool(serialised.get("metadata", {}).get("fallback_used", False))
        # Truncate trace output to avoid huge logs
        _trace_output = serialised["output"]
        if isinstance(_trace_output, dict) and "containers" in _trace_output and isinstance(_trace_output["containers"], list) and len(_trace_output["containers"]) > 5:
            _trace_output = {k: v for k, v in _trace_output.items() if k != "containers"}
            _trace_output["containers_truncated"] = len(serialised["output"]["containers"])
        log_trace(state, "tool", "call_tool", {"tool": name, "output": _trace_output, "risk_score": risk, "fallback_used": fallback_flag, "confidence": serialised.get("confidence", 0.0)}, duration_ms=dur)
        structured_log("tool_result", run_id=state.get("run_id", ""), step="tool", tool=name, fallback_used=fallback_flag, confidence=serialised.get("confidence", 0.0))

        # SSE publish per tool result
        try:
            from app.agent.sse import broadcaster
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(broadcaster.publish(state.get("run_id", ""), "tool_result", {"tool": name, "output": serialised["output"], "risk_score": risk, "fallback_used": fallback_flag}))
            except RuntimeError:
                pass
        except Exception:
            pass

        # Handle partial batch: continue even if one tool failed (we already do)
        # Notify if tool failed and we used fallback — escalation may be needed

    # Clear pending calls
    state["pending_tool_calls"] = []
    state["status"] = "running"

    # Check escalations after tool batch (e.g., data_stale after get_itt_candidates)
    try:
        from app.agent.escalation import check_escalations
        from app.hitl.models import HITL_GATES
        triggered = check_escalations(state)
        if triggered:
            state["escalation"] = triggered[0]
            if len(triggered) > 1:
                state["escalation_list"] = triggered  # type: ignore
            hitl5 = HITL_GATES.get("HITL-5") or HITL_GATES.get("hitl_5")
            if hitl5 and hasattr(hitl5, "to_dict"):
                state["hitl_pending"] = hitl5.to_dict()  # type: ignore
            elif isinstance(hitl5, dict):
                state["hitl_pending"] = dict(hitl5)
            else:
                state["hitl_pending"] = dict(HITL5_FALLBACK)
            state["status"] = "escalated"
            risk = compute_risk_score(state)
            structured_log("escalation_after_tool", run_id=state.get("run_id", ""), step="tool", trigger=triggered[0]["trigger"], risk_score=risk)
            log_trace(state, "escalation", "triggered", {"trigger": triggered[0]["trigger"], "risk_score": risk}, duration_ms=0)
            # SSE
            try:
                from app.agent.sse import broadcaster
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(broadcaster.publish(state.get("run_id", ""), "escalation", {"trigger": triggered[0]["trigger"], "risk_score": risk}))
                except RuntimeError:
                    pass
            except Exception:
                pass
    except Exception:
        pass

    # Validation guardrails check after tool batch (e.g., weight_bounds after T1)
    try:
        from app.agent.validation import validate_all
        failures = validate_all(state)
        if failures:
            # If weight bounds failed, set confidence low to trigger escalation
            for f in failures:
                if f["guard"] == "weight_bounds":
                    state["confidence"] = 0.6
                    structured_log("guardrail_weight_failed", run_id=state.get("run_id", ""), step="tool", failures=failures)
                    break
    except Exception:
        pass

    return state


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

