"""Execution trace + SSE publishing (Phase 6.8).

Every node appends a TraceEntry with risk_score. Includes deviation_log handling
and export_trace helper. Also publishes trace_entry events via the SSE broadcaster
singleton.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from app.agent.confidence import compute_risk_score
from app.shared.logging import structured_log


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_trace(
    state: dict[str, Any],
    node: str,
    action: str,
    result: dict[str, Any] | None = None,
    duration_ms: float = 0.0,
) -> dict[str, Any]:
    """Append a trace entry to state and publish via SSE broadcaster.

    The entry always contains risk_score (computed from current state).
    """
    if result is None:
        result = {}
    # Ensure result contains risk_score
    risk = compute_risk_score(state)
    if isinstance(result, dict) and "risk_score" not in result:
        result = {**result, "risk_score": risk}

    entry: dict[str, Any] = {
        "timestamp": _now_iso(),
        "run_id": state.get("run_id", ""),
        "node": node,
        "action": action,
        "result": result,
        "duration_ms": float(duration_ms),
        "confidence": float(state.get("confidence", 0.0)),
        "risk_score": float(risk),
    }
    trace = state.setdefault("trace", [])
    trace.append(entry)

    # Structured logging
    try:
        structured_log(
            "trace",
            run_id=state.get("run_id", ""),
            step=f"{node}:{action}",
            node=node,
            action=action,
            result=result,
            duration_ms=duration_ms,
            confidence=entry["confidence"],
            risk_score=risk,
        )
    except Exception:
        pass

    # SSE publish — via singleton broadcaster (not state)
    try:
        from app.agent.sse import broadcaster  # singleton

        # Use create_task if loop running, else direct await would block
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcaster.publish(state.get("run_id", ""), "trace_entry", entry))
        except RuntimeError:
            # No running loop (tests) — skip async publish
            pass
    except Exception:
        pass

    return entry


def export_trace(state: dict[str, Any]) -> dict[str, Any]:
    """Export full trace with summary (includes deviation_log + risk trajectory)."""
    trace = state.get("trace", []) or []
    deviation_log = state.get("deviation_log", []) or []

    # Normalise entries to dicts
    entries = []
    for e in trace:
        if isinstance(e, dict):
            entries.append(e)
        else:
            # dataclass with to_dict
            try:
                entries.append(e.to_dict())  # type: ignore
            except Exception:
                entries.append(dict(e))

    total_duration = sum(float(e.get("duration_ms", 0) or 0) for e in entries)
    confidence_trajectory = [float(e.get("confidence", 0) or 0) for e in entries]
    risk_trajectory = [float(e.get("risk_score", 0) or 0) for e in entries]

    return {
        "run_id": state.get("run_id", ""),
        "entries": entries,
        "deviation_log": deviation_log,
        "summary": {
            "total_steps": len(entries),
            "total_duration_ms": total_duration,
            "tools_called": [e for e in entries if e.get("node") == "tool"],
            "hitl_events": [e for e in entries if e.get("node") == "hitl"],
            "escalations": [e for e in entries if e.get("node") == "escalation"],
            "deviations": deviation_log,
            "confidence_trajectory": confidence_trajectory,
            "risk_trajectory": risk_trajectory,
        },
    }
