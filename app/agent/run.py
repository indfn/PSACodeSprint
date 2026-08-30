"""Agent run helpers — create_initial_state, run_agent, resume_agent (Phase 6.9)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from langgraph.types import Command

from app.agent.graph import build_graph
from app.agent.trace import export_trace
from app.shared.logging import structured_log


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_initial_state(event: Any, run_id: str) -> dict[str, Any]:
    """Create charter 11-field bootstrap state from ITTCoordinationEvent.

    Validates container_count >=50 and vessel departure in future.
    """
    # Normalise event to dict
    if hasattr(event, "model_dump"):
        ed = event.model_dump()  # Pydantic
    elif isinstance(event, dict):
        ed = dict(event)
    else:
        ed = dict(event)

    # Validations
    cc = ed.get("container_count", 0)
    if isinstance(cc, int) and cc < 50:
        raise ValueError(f"container_count must be >= 50, got {cc}")

    tuas_dep = ed.get("tuas_vessel_departure", "")
    if tuas_dep:
        try:
            vd = datetime.fromisoformat(str(tuas_dep).replace("Z", "+00:00"))
            if vd.tzinfo is None:
                vd = vd.replace(tzinfo=timezone.utc)
            if vd <= datetime.now(timezone.utc) + timedelta(minutes=30):
                raise ValueError(f"tuas_vessel_departure {tuas_dep} must be > now + 30min (A-21)")
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"invalid tuas_vessel_departure: {exc}") from exc

    # Load problem config for PB-12 by default (or active)
    problem_config: Any = {}
    try:
        from app.configs.problem_config import load_problem_config
        from app.agent.problem_switcher import get_active_problem_id
        pid = get_active_problem_id()
        problem_config = load_problem_config(pid)
    except Exception:
        try:
            from app.configs.problem_config import load_problem_config
            problem_config = load_problem_config("pb-12-itt")
        except Exception:
            problem_config = {}

    # Normalise problem_config to dict for state storage (serializable)
    if problem_config and not isinstance(problem_config, dict):
        # Convert dataclass to dict-like via raw
        raw = getattr(problem_config, "raw", None)
        if raw:
            pcs = raw
        else:
            # Build minimal dict
            pcs = {
                "problem": {"id": getattr(getattr(problem_config, "problem", None), "id", "pb-12-itt")},
                "systems": [],
                "tools": [],
                "cost_params": getattr(problem_config, "cost_params", {}),
            }
        problem_config = pcs if isinstance(pcs, dict) else {}

    context: dict[str, Any] = {
        "event": ed,
        "origin_terminal": ed.get("origin_terminal", "PPT"),
        "destination_terminal": ed.get("destination_terminal", "TUAS"),
        "vessel_id": ed.get("vessel_id", "MV PACIFIC STAR"),
        "container_count": ed.get("container_count", 120),
        "tuas_vessel_departure": ed.get("tuas_vessel_departure", "2026-08-19T20:00:00+08:00"),
        "blocks_affected": ed.get("blocks_affected", ["B-07", "B-08", "B-12", "B-14"]),
        "dg_containers": ed.get("dg_containers", 0),
        "priority_containers": ed.get("priority_containers", 0),
        "requested_by": ed.get("requested_by", ""),
        "current_step": "ingest",
        "candidates": None,
        "road_capacity": None,
        "sea_capacity": None,
        "split_result": None,
        "split_alternatives": [],
        "dispatched": False,
        "monitored": False,
        "constraints": (problem_config.get("constraints", {}) if isinstance(problem_config, dict) else {}),
    }

    # Pull confidence from active scenario (set by set_scenario before run_agent)
    initial_confidence = 0.85
    try:
        from app.mocks.scenarios import _active_scenario_id, _active_problem_id, _rng, PB12_SCENARIOS, PB01_SCENARIOS
        scenario_map = PB12_SCENARIOS if "pb-12" in _active_problem_id else PB01_SCENARIOS
        sc = scenario_map.get(_active_scenario_id)
        if sc is not None:
            initial_confidence = sc.confidence_initial.sample(_rng)
    except Exception:
        pass

    state: dict[str, Any] = {
        "messages": [{"role": "user", "content": f"ITT coordination request: {ed}"}],
        "tool_results": {},
        "pending_tool_calls": [],
        "hitl_pending": None,
        "hitl_history": [],
        "confidence": initial_confidence,
        "escalation": None,
        "trace": [],
        "deviation_log": [],
        "problem_config": problem_config,
        "problem_id": (problem_config.get("problem", {}).get("id", "pb-12-itt") if isinstance(problem_config, dict) else "pb-12-itt"),
        "run_id": run_id,
        "status": "running",
        "context": context,
    }
    return state


async def run_agent(event: Any, broadcaster: Any | None = None, run_id: str | None = None) -> dict[str, Any]:
    """Run agent from webhook event.

    Args:
        event: ITTCoordinationEvent
        broadcaster: Optional SSEBroadcaster singleton (ignored — graph nodes use singleton import)
        run_id: Optional run_id to use (caller-provided for SSE alignment)

    Returns:
        {"run_id": ..., "state": ..., "trace": ...}
    """
    if not run_id:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
    initial_state = create_initial_state(event, run_id)
    config = {"configurable": {"thread_id": run_id}}

    graph = build_graph()

    # Broadcaster is singleton at app.agent.sse.broadcaster — nodes import it directly,
    # not via state (avoids checkpoint serialization)
    structured_log("run_agent_start", run_id=run_id, step="init", vessel_id=initial_state["context"].get("vessel_id"))

    try:
        # Use ainvoke so interrupts work correctly
        result = await graph.ainvoke(initial_state, config=config)
    except Exception as exc:
        structured_log("run_agent_error", run_id=run_id, step="graph", error=str(exc))
        raise

    # Determine if interrupted (graph will have __interrupt__ in state?)
    # LangGraph's ainvoke returns state dict; if hitl_node interrupted, the result will be the state before interrupt
    # and the checkpointer stores the interrupt. We need to detect pending interrupt by checking hitl_pending
    # But after ainvoke with interrupt, the graph actually pauses and ainvoke returns the state up to the interrupt.
    # For our graph, hitl_node uses `interrupt()` which will cause ainvoke to raise or return with interrupt info.
    # The MemorySaver checkpoint stores the interrupt; the caller needs to check graph.get_state.

    # Check for interrupt via get_state
    try:
        snapshot = graph.get_state(config)  # type: ignore
        # snapshot.values is state; snapshot.interrupts holds interrupt payload
        # Check for pending interrupts
        interrupts = getattr(snapshot, "interrupts", None) or getattr(snapshot, "tasks", None)
        # More reliable: check if next node is hitl
        next_nodes = getattr(snapshot, "next", None)
        if next_nodes and "hitl" in next_nodes:
            # We are paused at HITL — return with hitl_card hint
            hitl_pending = result.get("hitl_pending") if isinstance(result, dict) else None
            card = None
            if hitl_pending:
                try:
                    from app.hitl.gates import build_approval_card
                    card = build_approval_card(hitl_pending, result)
                except Exception:
                    card = hitl_pending
            return {"run_id": run_id, "state": result, "trace": export_trace(result), "status": "waiting_hitl", "hitl_card": card, "hitl_pending": hitl_pending}
    except Exception:
        pass

    # Check if state has hitl_pending set (but not yet interrupted due to router)
    if isinstance(result, dict) and result.get("hitl_pending"):
        card = None
        try:
            from app.hitl.gates import build_approval_card
            card = build_approval_card(result["hitl_pending"], result)
        except Exception:
            card = result["hitl_pending"]
        return {"run_id": run_id, "state": result, "trace": export_trace(result), "status": "waiting_hitl", "hitl_card": card, "hitl_pending": result["hitl_pending"]}

    final_status = result.get("status", "completed") if isinstance(result, dict) else "completed"
    if final_status == "running" and isinstance(result, dict) and not result.get("hitl_pending") and not result.get("escalation"):
        final_status = "completed"
        try:
            result["status"] = "completed"
        except Exception:
            pass
    try:
        if final_status == "completed":
            import asyncio
            from app.agent.sse import broadcaster
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(broadcaster.publish(run_id, "run_complete", {"status": final_status, "run_id": run_id}))
                loop.create_task(broadcaster.publish(run_id, "trace_entry", {"node": "graph", "action": "completed", "result": {"status": final_status}}))
            except RuntimeError:
                pass
    except Exception:
        pass
    return {"run_id": run_id, "state": result, "trace": export_trace(result), "status": final_status}


async def resume_agent(run_id: str, decision: dict[str, Any]) -> dict[str, Any]:
    """Resume agent after HITL decision via Command(resume=).

    Args:
        run_id: The thread_id from run_agent
        decision: Dict with decision = approve|reject|modify, plus optional reason/modifications

    Returns:
        Same shape as run_agent, but may still be waiting_hitl if another gate fired.
    """
    from app.agent.resilience import is_hitl_stale

    graph = build_graph()
    config = {"configurable": {"thread_id": run_id}}

    # Load snapshot to check staleness
    try:
        snapshot = graph.get_state(config)  # type: ignore
        state_vals = getattr(snapshot, "values", {}) or {}
        if not state_vals:
            # Try alternate access
            state_vals = snapshot  # type: ignore
        # Check stale
        if is_hitl_stale(state_vals if isinstance(state_vals, dict) else {}, decision.get("gate_id") if isinstance(decision, dict) else None):
            # Return stale error instead of resuming
            return {"run_id": run_id, "state": state_vals, "status": "stale", "error": f"HITL {decision.get('gate_id','')} already timed out → {state_vals.get('status')}", "trace": export_trace(state_vals) if isinstance(state_vals, dict) else {}}
    except Exception:
        pass

    # Normal resume
    structured_log("resume_agent", run_id=run_id, step="hitl", decision=decision.get("decision") if isinstance(decision, dict) else str(decision))

    try:
        # LangGraph expects Command(resume=decision)
        result = await graph.ainvoke(Command(resume=decision), config=config)  # type: ignore
    except Exception as exc:
        structured_log("resume_agent_error", run_id=run_id, step="hitl", error=str(exc))
        raise

    # Check if still interrupted at next HITL
    try:
        snapshot = graph.get_state(config)  # type: ignore
        next_nodes = getattr(snapshot, "next", None)
        if next_nodes and "hitl" in next_nodes:
            hitl_pending = result.get("hitl_pending") if isinstance(result, dict) else None
            card = None
            if hitl_pending:
                try:
                    from app.hitl.gates import build_approval_card
                    card = build_approval_card(hitl_pending, result)
                except Exception:
                    card = hitl_pending
            return {"run_id": run_id, "state": result, "trace": export_trace(result), "status": "waiting_hitl", "hitl_card": card, "hitl_pending": hitl_pending}
    except Exception:
        pass

    if isinstance(result, dict) and result.get("hitl_pending"):
        card = None
        try:
            from app.hitl.gates import build_approval_card
            card = build_approval_card(result["hitl_pending"], result)
        except Exception:
            card = result["hitl_pending"]
        return {"run_id": run_id, "state": result, "trace": export_trace(result), "status": "waiting_hitl", "hitl_card": card, "hitl_pending": result["hitl_pending"]}

    final_status = result.get("status", "completed") if isinstance(result, dict) else "completed"
    if final_status == "running" and isinstance(result, dict) and not result.get("hitl_pending") and not result.get("escalation"):
        final_status = "completed"
        try:
            result["status"] = "completed"
        except Exception:
            pass
    try:
        if final_status == "completed":
            import asyncio
            from app.agent.sse import broadcaster
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(broadcaster.publish(run_id, "run_complete", {"status": final_status, "run_id": run_id}))
            except RuntimeError:
                pass
    except Exception:
        pass
    return {"run_id": run_id, "state": result, "trace": export_trace(result), "status": final_status}
