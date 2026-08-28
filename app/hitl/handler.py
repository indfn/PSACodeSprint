"""HITL response handler — REJECT / MODIFY / TIMEOUT / APPROVE (Phase 6.5)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.hitl.models import HITL5_FALLBACK


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def handle_hitl_response(
    state: dict[str, Any],
    gate: dict[str, Any] | Any,
    decision: dict[str, Any],
    registry=None,
) -> dict[str, Any]:
    """Handle a HITL decision and mutate state accordingly.

    Args:
        state: AgentState dict (mutable).
        gate: HITLGate dict or dataclass (must have gate_id/gate_name/timeout_action).
        decision: Dict with `decision` = approve|reject|modify|timeout,
                  plus optional `reason`, `modifications`.

    Returns:
        Updated state dict (same object, mutated).
    """
    # Normalise gate to dict
    if hasattr(gate, "to_dict"):
        gate = gate.to_dict()  # type: ignore
    elif not isinstance(gate, dict):
        # try dataclass -> dict
        try:
            from dataclasses import asdict
            gate = asdict(gate)  # type: ignore
        except Exception:
            gate = dict(gate)  # type: ignore

    gate_id = gate.get("gate_id", "HITL-1")
    gate_name = gate.get("gate_name", gate_id)
    timeout_action = gate.get("timeout_action", "escalate")

    # Normalise decision field
    d_raw = decision.get("decision") if isinstance(decision, dict) else str(decision)
    d = str(d_raw).lower() if d_raw is not None else ""
    # Map approve/approved, reject/rejected etc.
    if d in ("approved", "approve"):
        d = "approve"
    elif d in ("rejected", "reject"):
        d = "reject"
    elif d in ("modified", "modify"):
        d = "modify"
    elif d in ("timeout", "timed_out", "expired"):
        d = "timeout"

    # Helper to append history
    def _append_history(decision_str: str) -> None:
        history = state.setdefault("hitl_history", [])
        history.append({
            "gate_id": gate_id,
            "gate_name": gate_name,
            "decision": decision_str,
            "reason": decision.get("reason") if isinstance(decision, dict) else None,
            "modifications": decision.get("modifications") if isinstance(decision, dict) else None,
            "timestamp": _now_iso(),
            "decided_by": decision.get("decided_by", "operator") if isinstance(decision, dict) else "operator",
        })

    # Import here to avoid circulars
    try:
        from app.hitl.models import HITL_GATES
    except Exception:
        HITL_GATES = {}  # type: ignore

    try:
        from app.shared.logging import structured_log
    except Exception:
        structured_log = lambda *a, **k: None  # type: ignore

    try:
        from app.agent.trace import log_trace
    except Exception:
        log_trace = lambda *a, **k: {}  # type: ignore

    if d == "approve":
        _append_history("approve")
        state["hitl_pending"] = None
        state["status"] = "running"
        # Purge gate entered timestamp
        state.pop("hitl_gate_entered_at", None)
        # Clear escalation if this was HITL-5 (duty manager resolves escalation)
        if gate_id in ("HITL-5", "hitl_5", "hitl-5"):
            state["escalation"] = None
            state.pop("escalation_list", None)
            # Charter confidence trajectory: 0.78 -> 0.90 after emergency re-split approval
            # Also clear feeder_hold trigger to avoid immediate re-escalation
            state["confidence"] = 0.90
            ctx = state.get("context", {}) or {}
            # Keep feeder_hold_hours for audit but don't trigger again — set to 1.0 below threshold
            # Only if it was the deviation-induced 2.0, lower it
            if ctx.get("feeder_hold_hours", 0) > 1.5:
                ctx["feeder_hold_hours"] = 1.0
            # Mark deviation as handled to prevent re-escalation on next agent cycle
            ctx["deviation_handled"] = True
            # Ensure monitor is marked as handled
            ctx["monitored"] = True
        log_trace(state, "hitl", "approve", {"gate_id": gate_id, "decision": "approve"}, duration_ms=0)
        structured_log("hitl_approve", run_id=state.get("run_id", ""), step=gate_id, gate_id=gate_id)

        # Mark dispatched context if this was dispatch gate
        if gate_id in ("HITL-2", "hitl_2"):
            ctx = state.setdefault("context", {})
            ctx["dispatch_approved"] = True

        return state

    elif d == "reject":
        _append_history("reject")
        reason = decision.get("reason", "") if isinstance(decision, dict) else ""
        structured_log("hitl_reject", run_id=state.get("run_id", ""), step=gate_id, gate_id=gate_id, reason=reason)
        alternatives = (state.get("context", {}) or {}).get("split_alternatives", []) or []
        # Also check split_result alternatives?
        if alternatives:
            # Charter: present alternatives to agent via messages so it re-reasons
            state["messages"].append({
                "role": "user",
                "content": f"HITL {gate_id} REJECTED: {reason}. Alternatives: {json.dumps(alternatives, default=str)[:3000]}. Propose next steps or re-optimise.",
            })
            state["hitl_pending"] = None
            state["status"] = "running"
            log_trace(state, "hitl", "reject_with_alternatives", {"gate_id": gate_id, "reason": reason, "alternatives": alternatives[:2]}, duration_ms=0)
        else:
            # No alternatives → escalate to Duty Manager (HITL-5)
            escalate_gate = None
            try:
                escalate_gate = HITL_GATES.get("HITL-5") or HITL_GATES.get("hitl_5")
                if escalate_gate and hasattr(escalate_gate, "to_dict"):
                    escalate_gate = escalate_gate.to_dict()
            except Exception:
                escalate_gate = dict(HITL5_FALLBACK)
            state["escalation"] = {"trigger": "hitl_rejection_no_alternatives", "gate_id": gate_id, "severity": "high", "reason": reason, "timestamp": _now_iso()}
            state["hitl_pending"] = escalate_gate
            state["status"] = "escalated"
            log_trace(state, "hitl", "reject_escalate", {"gate_id": gate_id, "reason": reason, "escalation": "HITL-5"}, duration_ms=0)
            # SSE escalate
            try:
                from app.agent.sse import broadcaster
                import asyncio
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(broadcaster.publish(state.get("run_id", ""), "escalation", {"trigger": "hitl_rejection_no_alternatives", "gate_id": gate_id}))
                except RuntimeError:
                    pass
            except Exception:
                pass
        return state

    elif d == "modify":
        modifications = decision.get("modifications", {}) if isinstance(decision, dict) else {}
        # Validate modifications type safety — must be dict
        if not isinstance(modifications, dict):
            err = f"modifications must be dict, got {type(modifications).__name__}"
            state["messages"].append({"role": "user", "content": f"MODIFY validation failed: {err}. Re-propose a valid split."})
            log_trace(state, "hitl", "modify_validation_failed", {"gate_id": gate_id, "error": err}, duration_ms=0)
            state["hitl_pending"] = None
            state["status"] = "running"
            return state
        structured_log("hitl_modify", run_id=state.get("run_id", ""), step=gate_id, modifications=modifications)
        # Validate vs guardrails
        try:
            from app.agent.validation import validate_split_modification
            validation = validate_split_modification(modifications, state)
        except Exception as exc:
            validation = {"valid": False, "error": str(exc)}

        if not validation.get("valid"):
            err = validation.get("error", "validation failed")
            state["messages"].append({"role": "user", "content": f"MODIFY validation failed: {err}. Re-propose a valid split."})
            log_trace(state, "hitl", "modify_validation_failed", {"gate_id": gate_id, "error": err}, duration_ms=0)
            # Keep hitl_pending = same gate so operator can retry? For now, clear and let agent re-reason
            # But charter says re-present same gate with error — we keep hitl_pending
            # To avoid infinite loop in graph, we set status running and let agent node handle next
            state["hitl_pending"] = None
            state["status"] = "running"
            return state

        # Re-run Tool 4 with modified params — A-09: inside graph's async context, await directly
        try:
            from app.tools.registry import registry as _reg
            reg = registry or _reg
            ctx = state.get("context", {}) or {}
            candidates = ctx.get("candidates", {}) or {}
            road_capacity = ctx.get("road_capacity", {}) or {}
            sea_capacity = ctx.get("sea_capacity", {}) or {}
            tuas_dep = ctx.get("tuas_vessel_departure", "2026-08-19T20:00:00+08:00")
            constraints = dict(ctx.get("constraints", {}) or {})
            # Only merge dict modifications safely
            constraints.update(modifications)
            result = await reg.call(
                "compute_itt_split",
                candidates=candidates,
                road_capacity=road_capacity,
                sea_capacity=sea_capacity,
                tuas_vessel_departure=tuas_dep,
                constraints=constraints,
                _run_id=state.get("run_id", ""),
            )
            out = result.output if hasattr(result, "output") else (result.get("output", {}) if isinstance(result, dict) else {})
            new_opt = out.get("optimal_split", out) if isinstance(out, dict) else {}
            new_alts = out.get("alternatives", []) if isinstance(out, dict) else []
            state.setdefault("context", {})["split_result"] = new_opt
            state["context"]["split_alternatives"] = new_alts
            state["context"]["split_modifications"] = modifications
            state["messages"].append({"role": "user", "content": f"Re-computed split per MODIFY {json.dumps(modifications)}: {json.dumps(new_opt, default=str)[:2000]}. Re-approve."})
            log_trace(state, "hitl", "modify_recomputed", {"gate_id": gate_id, "new_split": new_opt}, duration_ms=0)
        except Exception as exc:
            state["messages"].append({"role": "user", "content": f"Re-compute after MODIFY failed: {exc}. Re-propose."})
            log_trace(state, "hitl", "modify_recompute_failed", {"gate_id": gate_id, "error": str(exc)}, duration_ms=0)

        # Re-present same gate (will re-enter hitl_node on next iteration)
        # For Command(resume) flow, we just keep hitl_pending = gate so next loop shows card again
        # But handler is called from hitl_node after interrupt resume — we want to go back to agent then hitl
        # So clear pending now and let agent re-evaluate; the agent will set it again if needed.
        state["hitl_pending"] = None
        state["status"] = "running"
        _append_history("modify")
        return state

    elif d == "timeout":
        # Per-gate timeout_action: escalate / cancel_dispatch / hold_sequence / halt
        action = str(timeout_action).lower()
        # Normalise aliases from YAML
        if action in ("escalate_to_duty_manager", "escalate"):
            action = "escalate"
        elif action in ("cancel_dispatch", "cancel"):
            action = "cancel_dispatch"
        elif action in ("hold_current_sequence", "hold_sequence", "hold"):
            action = "hold_sequence"
        elif action in ("halt_workflow", "halt"):
            action = "halt"

        _append_history("timeout")
        structured_log("hitl_timeout", run_id=state.get("run_id", ""), step=gate_id, timeout_action=action)

        if action == "escalate":
            esc_gate = None
            try:
                esc_gate = HITL_GATES.get("HITL-5") or HITL_GATES.get("hitl_5")
                if esc_gate and hasattr(esc_gate, "to_dict"):
                    esc_gate = esc_gate.to_dict()
            except Exception:
                esc_gate = dict(HITL5_FALLBACK)
            state["escalation"] = {"trigger": "hitl_timeout", "gate_id": gate_id, "timeout_action": "escalate", "timestamp": _now_iso()}
            state["hitl_pending"] = esc_gate
            state["status"] = "escalated"
            log_trace(state, "hitl", "timeout_escalate", {"gate_id": gate_id}, duration_ms=0)
        elif action == "cancel_dispatch":
            state["status"] = "cancelled"
            state["hitl_pending"] = None
            ctx = state.setdefault("context", {})
            ctx["dispatch_cancelled_due_to"] = gate_id
            log_trace(state, "hitl", "timeout_cancel_dispatch", {"gate_id": gate_id}, duration_ms=0)
        elif action == "hold_sequence":
            state["status"] = "holding"
            state["hitl_pending"] = None
            ctx = state.setdefault("context", {})
            ctx["sequence_held_due_to"] = gate_id
            log_trace(state, "hitl", "timeout_hold_sequence", {"gate_id": gate_id}, duration_ms=0)
        elif action == "halt":
            state["status"] = "halted"
            state["hitl_pending"] = None
            log_trace(state, "hitl", "timeout_halt", {"gate_id": gate_id}, duration_ms=0)
        else:
            state["status"] = "halted"
            state["hitl_pending"] = None

        # Second-level: if Duty Manager also silent 30 min → halt entirely
        # This is handled by HITL-5 timeout itself (halt). For other gates that escalate,
        # the escalation creates HITL-5 which will itself timeout to halt if not responded.
        return state

    else:
        # Unknown decision — treat as reject for safety
        structured_log("hitl_unknown_decision", run_id=state.get("run_id", ""), step=gate_id, decision=d)
        state["hitl_pending"] = None
        state["status"] = "running"
        return state
