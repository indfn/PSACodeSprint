"""Single hitl_node using LangGraph interrupt() + Command(resume=) (Phase 6.5)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langgraph.types import interrupt, Command


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_risk_score_for_card(state: dict[str, Any]) -> float:
    try:
        from app.agent.confidence import compute_risk_score
        return compute_risk_score(state)
    except Exception:
        return round(1.0 - float(state.get("confidence", 1.0)), 3)


def build_approval_card(gate: dict[str, Any] | Any, state: dict[str, Any]) -> dict[str, Any]:
    """Build structured approval card per charter §4 template."""
    if hasattr(gate, "to_dict"):
        gate = gate.to_dict()  # type: ignore
    elif not isinstance(gate, dict):
        try:
            from dataclasses import asdict
            gate = asdict(gate)  # type: ignore
        except Exception:
            gate = dict(gate)  # type: ignore

    gate_id = gate.get("gate_id", "HITL-1")
    gate_name = gate.get("gate_name", gate_id)
    timeout_seconds = int(gate.get("timeout_seconds", 1800))
    timeout_action = gate.get("timeout_action", "escalate")
    triggered_at_stage = gate.get("triggered_at_stage", "") if isinstance(gate, dict) else ""

    context = state.get("context", {}) or {}
    split_result = context.get("split_result", {}) or {}
    # alternatives from context
    alternatives = context.get("split_alternatives", []) or []
    # cost breakdown
    cost_summary: dict[str, Any] = {}
    if isinstance(split_result, dict):
        cost_summary = {
            "optimal_split": split_result,
            "cost_vs_baseline": context.get("cost_vs_baseline", {}),
            "roi": context.get("roi", {}),
        }
    # margin
    timeline = context.get("timeline", {}) or {}
    margin_minutes = timeline.get("margin_minutes", timeline.get("margin", 0))
    # fallback: try split_result timeline
    if not margin_minutes and isinstance(context.get("split_result"), dict):
        margin_minutes = 0

    confidence = float(state.get("confidence", 0.0))
    risk_score = compute_risk_score_for_card(state)

    card: dict[str, Any] = {
        "gate_id": gate_id,
        "gate_name": gate_name,
        "trigger": gate.get("trigger", ""),
        "cost_breakdown": cost_summary,
        "optimal_split": split_result,
        "alternatives": alternatives[:3] if isinstance(alternatives, list) else [],
        "confidence": confidence,
        "risk_score": risk_score,
        "margin_minutes": margin_minutes,
        "timeout_seconds": timeout_seconds,
        "timeout_action": timeout_action,
        "timestamp": _now_iso(),
        "problem_id": state.get("problem_id", state.get("run_id", "")),
        "triggered_at_stage": triggered_at_stage,
    }

    # Gate-specific data from context
    gid_norm = gate_id.lower().replace("-", "_")
    if gid_norm in ("hitl_2",):
        dispatch = context.get("dispatch_result", {}) or {}
        if isinstance(dispatch, dict):
            card["dispatch"] = {
                "dispatch_id": dispatch.get("dispatch_id", ""),
                "num_trucks": dispatch.get("num_trucks", 0),
                "route": dispatch.get("route", ""),
                "container_count": dispatch.get("container_count", 0),
                "total_trips": dispatch.get("total_trips", 0),
                "eta": dispatch.get("eta", ""),
                "dispatch_cost": dispatch.get("cost", 0),
                "truck_assignments": dispatch.get("truck_assignments", []),
            }
    elif gid_norm in ("hitl_3",):
        hold = context.get("feeder_hold_result", {}) or {}
        if isinstance(hold, dict):
            card["feeder_hold"] = {
                "feeder_id": hold.get("feeder_id", ""),
                "hold_hours": hold.get("hold_hours", 0),
                "hold_cost": hold.get("hold_cost", 0),
                "hold_cost_per_hour": hold.get("hold_cost_per_hour", 800),
                "new_departure": hold.get("new_departure", ""),
                "previous_departure": hold.get("previous_departure", ""),
                "tidal_risk": hold.get("tidal_risk", "safe"),
                "operator_response": hold.get("operator_response", ""),
            }
    elif gid_norm in ("hitl_4",):
        seq = context.get("tuas_sequence", {}) or {}
        if isinstance(seq, dict):
            card["tuas_sequence"] = {
                "vessel_id": seq.get("vessel_id", ""),
                "updated_loading_sequence": seq.get("updated_loading_sequence", ""),
                "qc_adjustments": seq.get("qc_adjustments", []),
                "estimated_loading_completion": seq.get("estimated_loading_completion", ""),
                "margin_before_departure_minutes": seq.get("margin_before_departure_minutes", 0),
            }
    elif gid_norm in ("hitl_5",):
        devs = state.get("deviation_log", [])
        dev = devs[-1] if isinstance(devs, list) and devs else {}
        card["deviation"] = dev
        card["is_emergency"] = True
        # Merge emergency card data from monitor.py build_emergency_resplit_card()
        # These fields are stored in gate["approval_card"] by monitor_node
        emergency = gate.get("approval_card") if isinstance(gate, dict) else None
        if isinstance(emergency, dict):
            for key in ("previous_split", "new_split", "cost_impact", "delta_trucks", "reason", "title"):
                if key in emergency and emergency[key]:
                    card[key] = emergency[key]
        # Adaptable per-trigger details (YAML-driven) from agent/tool/monitor
        for key in ("escalation_details", "escalation_kind", "agent_reasoning", "missing_data_notice", "validation_notes", "triggered_at_stage", "trigger"):
            if isinstance(gate, dict) and key in gate and gate[key]:
                card[key] = gate[key]

    # Add emergency fields if deviation exists (for any gate)
    if not card.get("is_emergency") and state.get("deviation_log"):
        card["deviation"] = state["deviation_log"][-1] if isinstance(state["deviation_log"], list) else state["deviation_log"]

    return card


async def hitl_node(state: dict[str, Any]) -> dict[str, Any] | Command:
    """Single HITL node — publishes card via SSE, then interrupt().

    The graph's checkpointer (MemorySaver + thread_id) ensures this pauses until
    `graph.ainvoke(Command(resume=decision), config=thread_cfg)` resumes it.
    """
    gate = state.get("hitl_pending")
    if not gate:
        # No gate — just pass through to agent
        return state  # type: ignore

    # Normalise gate for card building
    card = build_approval_card(gate, state)
    gate_id = card["gate_id"]
    gate_name = card["gate_name"]
    timeout_seconds = card["timeout_seconds"]
    timeout_action = card["timeout_action"]
    confidence = card["confidence"]
    risk_score = card["risk_score"]

    # Record when gate was entered (for stale detection)
    state["hitl_gate_entered_at"] = _now_iso()
    state["status"] = "waiting_hitl"

    # Publish via singleton broadcaster + trace
    try:
        from app.agent.sse import broadcaster

        import asyncio

        payload = {
            "gate_id": gate_id,
            "gate_name": gate_name,
            "approval_card": card,
            "confidence": confidence,
            "risk_score": risk_score,
            "timeout_seconds": timeout_seconds,
            "timeout_action": timeout_action,
        }
        # fire and forget — broadcaster.publish is async
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcaster.publish(state.get("run_id", ""), "hitl_card", payload))
        except RuntimeError:
            # No loop in sync context — try to publish via asyncio.run in thread? skip for tests
            pass
    except Exception:
        pass

    # Trace
    try:
        from app.agent.trace import log_trace

        log_trace(state, "hitl", "show_card", {"gate_id": gate_id, "gate_name": gate_name, "risk_score": risk_score, "confidence": confidence}, duration_ms=0)
    except Exception:
        pass

    try:
        from app.shared.logging import structured_log

        structured_log("hitl_card", run_id=state.get("run_id", ""), step=gate_id, gate_id=gate_id, gate_name=gate_name, confidence=confidence, risk_score=risk_score)
    except Exception:
        pass

    # LangGraph interrupt — pauses graph until Command(resume=...) resumes
    # Payload is the canonical interrupt shape: frontend reads BOTH top-level and card-level
    interrupt_payload = {
        "gate_id": gate_id,
        "gate_name": gate_name,
        "approval_card": card,
        "confidence": confidence,
        "risk_score": risk_score,
        "timeout_seconds": timeout_seconds,
        "timeout_action": timeout_action,
    }

    # Schedule timeout — task starts counting immediately; will fire during
    # the interrupt pause if not cancelled by a manual decision first.
    # The handler's TOCTOU guard (gate_id + hitl_pending check) ensures it
    # only fires for the correct, still-pending gate.
    from app.hitl.timeout_scheduler import schedule_timeout
    schedule_timeout(state.get("run_id", ""), gate_id, timeout_seconds, state, gate)

    # This line pauses execution; upon resume, decision is the value passed to Command(resume=...)
    decision = interrupt(interrupt_payload)  # type: ignore

    # Cancel timeout on manual decision
    from app.hitl.timeout_scheduler import cancel_timeout
    cancel_timeout(state.get("run_id", ""), gate_id)

    # Guard: stale resume via single resilience helper (normalizes HITL-1 == hitl_1, checks TTL)
    try:
        from app.agent.resilience import is_hitl_stale
        if is_hitl_stale(state, gate_id):
            try:
                from app.agent.trace import log_trace as _lt

                _lt(state, "hitl", "stale_resume_ignored", {"gate_id": gate_id, "decision": decision}, duration_ms=0)
            except Exception:
                pass
            return state  # type: ignore
    except Exception:
        # Fallback to legacy check
        if state.get("status") in ("halted", "cancelled", "holding") and state.get("hitl_pending") is None:
            try:
                from app.agent.trace import log_trace as _lt

                _lt(state, "hitl", "stale_resume_ignored", {"gate_id": gate_id, "decision": decision}, duration_ms=0)
            except Exception:
                pass
            return state  # type: ignore

    # Normal resume — handle decision via handler.py
    # handler mutates state and clears or escalates hitl_pending
    try:
        from app.hitl.handler import handle_hitl_response

        # Gate may have been mutated (e.g., HITL-5 re-used); pass original gate dict
        gate_for_handler = gate if isinstance(gate, dict) else gate  # keep as is
        # Normalise decision to dict form {"decision": "...", "reason": ..., "modifications": ...}
        if not isinstance(decision, dict):
            # Could be a plain string "approve", wrap it
            decision = {"decision": str(decision)}
        updated = await handle_hitl_response(state, gate_for_handler, decision)
        return updated  # type: ignore
    except Exception as exc:
        # On handler error, log and proceed to avoid graph crash
        try:
            from app.shared.logging import structured_log as _sl

            _sl("hitl_handler_error", run_id=state.get("run_id", ""), step=gate_id, error=str(exc))
        except Exception:
            pass
        state["hitl_pending"] = None
        state["status"] = "running"
        return state  # type: ignore
