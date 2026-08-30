"""Monitoring / Re-computation Loop — Steps 12–17 (Phase 6.10)."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from app.hitl.models import HITL5_FALLBACK


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def monitor_node(state: dict[str, Any]) -> dict[str, Any]:
    """Post-dispatch monitor: re-query T3, detect berth conflict, re-compute T4, set HITL-5."""
    ctx = state.setdefault("context", {})
    # deviation_handled guard to prevent re-triggering HITL-5 loop (>120s)
    if ctx.get("deviation_handled"):
        return state
    # Mark monitoring started
    if ctx.get("monitored"):
        # Already monitored — avoid loop
        return state
    ctx["monitored"] = True

    try:
        from app.agent.trace import log_trace
        log_trace(state, "monitor", "start", {"timestamp": _now_iso()}, duration_ms=0)
    except Exception:
        pass

    # Simulate monitoring query latency for demo
    try:
        from app.agent.mock_provider import _demo_delay
        _demo_delay("tool")
    except Exception:
        pass

    # Re-query T3 with current_time = now
    feeder_id = ctx.get("feeder_id", "FEEDER ATLANTIC-03")
    if not feeder_id:
        # Try from sea_capacity
        sc = ctx.get("sea_capacity", {}) or {}
        feeder_id = sc.get("feeder_id", "FEEDER ATLANTIC-03")

    try:
        from app.tools.registry import registry

        # Ensure registry has sea tool
        if not registry.get_tool("check_sea_itt_capacity"):
            try:
                from app.agent.problem_switcher import get_active_problem_id
                registry.register_for_problem(get_active_problem_id())
            except Exception:
                pass

        result = await registry.call("check_sea_itt_capacity", feeder_id=feeder_id, current_time=_now_iso(), _run_id=state.get("run_id", ""))
        current = result.output if hasattr(result, "output") else (result.get("output", {}) if isinstance(result, dict) else {})

        previous = ctx.get("sea_capacity", {}) or {}

        # Check for deviation: berth_status changed, departure delayed, tidal risk
        deviation = None
        berth_changed = False
        departure_changed = False

        curr_berth = str(current.get("berth_status", "")) if isinstance(current, dict) else ""
        prev_berth = str(previous.get("berth_status", "")) if isinstance(previous, dict) else ""
        if "conflict" in curr_berth.lower() and "conflict" not in prev_berth.lower():
            berth_changed = True

        curr_dw = current.get("departure_window", {}) if isinstance(current, dict) else {}
        prev_dw = previous.get("departure_window", {}) if isinstance(previous, dict) else {}
        if isinstance(curr_dw, dict) and isinstance(prev_dw, dict):
            if curr_dw.get("latest") != prev_dw.get("latest") and curr_dw.get("latest"):
                departure_changed = True

        if berth_changed or departure_changed:
            deviation = {
                "type": "feeder_berth_conflict",
                "previous_window": prev_dw if isinstance(prev_dw, dict) else previous.get("departure_window"),
                "current_window": curr_dw if isinstance(curr_dw, dict) else current.get("departure_window"),
                "previous_berth": prev_berth,
                "current_berth": curr_berth,
                "impact": "feeder delayed to 1600, may miss downstream tidal window",
                "detected_at": _now_iso(),
                "feeder_id": feeder_id,
            }
            # Append deviation_log
            state.setdefault("deviation_log", []).append(deviation)
            ctx["sea_capacity"] = current
            ctx["previous_sea_capacity"] = previous
            # Charter confidence trajectory: 0.95 -> 0.78 -> 0.90
            state["confidence"] = 0.78  # below 0.85 → triggers escalation #1

            # Publish confidence_update SSE event
            try:
                from app.agent.sse import broadcaster
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(broadcaster.publish(state.get("run_id", ""), "confidence_update", {"confidence": 0.78, "source": "monitor_deviation"}))
                except RuntimeError:
                    pass
            except Exception:
                pass

            ctx["feeder_hold_hours"] = 2.0  # above 1.5h → triggers escalation #2
            ctx["deviation_handled"] = False  # mark deviation detected, not yet handled (handler sets True after HITL-5)

            # Set escalation for berth conflict
            state["escalation"] = {"trigger": "feeder_berth_conflict", "deviation": deviation, "severity": "high", "timestamp": _now_iso(), "message": "Feeder berth conflict detected"}

            # Re-compute split with updated sea capacity
            candidates = ctx.get("candidates", {}) or {}
            road_cap = ctx.get("road_capacity", {}) or {}
            tuas_dep = ctx.get("tuas_vessel_departure", "2026-08-19T20:00:00+08:00")
            constraints = dict(ctx.get("constraints", {}) or {})
            # Include berth conflict flag so optimiser can pick 100/20 alternative
            constraints["berth_conflict"] = True

            # Save previous split for emergency card
            prev_split = ctx.get("split_result")
            ctx["previous_split"] = prev_split

            try:
                new_res = await registry.call("compute_itt_split", candidates=candidates, road_capacity=road_cap, sea_capacity=current, tuas_vessel_departure=tuas_dep, constraints=constraints, _run_id=state.get("run_id", ""))
                new_out = new_res.output if hasattr(new_res, "output") else (new_res.get("output", {}) if isinstance(new_res, dict) else {})
                if isinstance(new_out, dict):
                    opt = new_out.get("optimal_split", new_out)
                    # Optimiser now sea-limits to 20 when berth_conflict from live API data (total-20), no hardcoded 100/20 promotion
                    ctx["split_result"] = opt
                    ctx["split_alternatives"] = new_out.get("alternatives", [])
                    ctx["cost_vs_baseline"] = new_out.get("cost_vs_baseline", ctx.get("cost_vs_baseline", {}))
                    ctx["timeline"] = new_out.get("timeline", ctx.get("timeline", {}))
                    ctx["roi"] = new_out.get("roi", ctx.get("roi", {}))
            except Exception as exc:
                ctx["recompute_error"] = str(exc)

            # Route to emergency HITL-5
            try:
                from app.hitl.models import HITL_GATES
                hitl5 = HITL_GATES.get("HITL-5") or HITL_GATES.get("hitl_5")
                if hitl5 and hasattr(hitl5, "to_dict"):
                    pending = hitl5.to_dict()
                elif isinstance(hitl5, dict):
                    pending = dict(hitl5)
                else:
                    pending = dict(HITL5_FALLBACK)
                # Add emergency card data
                emergency_card = build_emergency_resplit_card(state, deviation)
                pending["approval_card"] = emergency_card
                pending["emergency"] = True
                pending["triggered_at_stage"] = "Monitor"
                pending["trigger"] = "feeder_berth_conflict"
                state["hitl_pending"] = pending
            except Exception:
                fb = {**HITL5_FALLBACK, "approval_card": build_emergency_resplit_card(state, deviation)}
                fb["triggered_at_stage"] = "Monitor"
                fb["trigger"] = "feeder_berth_conflict"
                state["hitl_pending"] = fb

            # Trace deviation
            try:
                from app.agent.trace import log_trace as _lt
                _lt(state, "monitor", "deviation_detected", {"deviation": deviation, "new_split": ctx.get("split_result", {}), "risk_score": 0.78}, duration_ms=0)
                from app.shared.logging import structured_log as _sl
                _sl("deviation_detected", run_id=state.get("run_id", ""), step="monitor", deviation=deviation, previous_window=deviation.get("previous_window"), current_window=deviation.get("current_window"))
                # SSE deviation
                from app.agent.sse import broadcaster
                import asyncio
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(broadcaster.publish(state.get("run_id", ""), "deviation", deviation))
                except RuntimeError:
                    pass
            except Exception:
                pass

            # Also check escalation triggers — ensure low_confidence + feeder_hold fire
            try:
                from app.agent.escalation import check_escalations
                triggered = check_escalations(state)
                if triggered:
                    # keep first escalation but also note all
                    state["escalation_list"] = triggered  # type: ignore
            except Exception:
                pass
        else:
            # No deviation
            try:
                from app.agent.trace import log_trace as _lt
                _lt(state, "monitor", "no_deviation", {"timestamp": _now_iso()}, duration_ms=0)
            except Exception:
                pass

        # Check data staleness trigger #4 while monitoring (if edge case injected)
        try:
            from app.agent.escalation import check_data_stale
            if check_data_stale(state):
                # If not already escalated, set data stale escalation
                if not state.get("escalation"):
                    state["escalation"] = {"trigger": "data_stale", "message": "Container data is stale (>30 min)", "severity": "high", "timestamp": _now_iso()}
                    try:
                        from app.hitl.models import HITL_GATES
                        hitl5 = HITL_GATES.get("HITL-5") or HITL_GATES.get("hitl_5")
                        if hitl5 and hasattr(hitl5, "to_dict"):
                            state["hitl_pending"] = hitl5.to_dict()  # type: ignore
                        elif isinstance(hitl5, dict):
                            state["hitl_pending"] = dict(hitl5)
                    except Exception:
                        pass
        except Exception:
            pass

    except Exception as exc:
        try:
            from app.shared.logging import structured_log as _sl
            _sl("monitor_error", run_id=state.get("run_id", ""), step="monitor", error=str(exc))
        except Exception:
            pass
        # Don't crash — return state

    return state


def build_emergency_resplit_card(state: dict[str, Any], deviation: dict[str, Any]) -> dict[str, Any]:
    ctx = state.get("context", {}) or {}
    prev = ctx.get("previous_split", {}) or {}
    new = ctx.get("split_result", {}) or {}
    cost_impact = "+$1,500 road cost but avoids $5,000 missed connection"
    try:
        prev_cost = prev.get("total_transport_cost", 10400) if isinstance(prev, dict) else 10400
        new_cost = new.get("total_transport_cost", 11200) if isinstance(new, dict) else 11200
        diff = new_cost - prev_cost if isinstance(new_cost, int) and isinstance(prev_cost, int) else 800
        cost_impact = f"+${diff} transport cost but avoids $5,000 missed connection"
    except Exception:
        pass
    delta_str = "+4 trucks (10 additional trips)"
    try:
        if isinstance(prev, dict) and isinstance(new, dict):
            prev_trips = int(prev.get("road_trips", 0) or 0)
            new_trips = int(new.get("road_trips", 0) or 0)
            d_trips = new_trips - prev_trips
            if d_trips > 0:
                # Trucks needed: ceil(trips / 2) assuming 2 trips per truck per wave, but at least 1
                d_trucks = max(1, (d_trips + 1) // 2)
                # Also consider container delta for display
                prev_road = int(prev.get("road_containers", 0) or 0)
                new_road = int(new.get("road_containers", 0) or 0)
                d_road = new_road - prev_road
                delta_str = f"+{d_trucks} trucks ({d_trips} additional trips, +{d_road} road containers)"
            elif d_trips < 0:
                delta_str = f"{d_trips} trips ({-d_trips} fewer)"
    except Exception:
        pass
    return {
        "title": "EMERGENCY RE-SPLIT REQUIRED",
        "reason": deviation.get("impact", "Feeder berth conflict — re-split required"),
        "previous_split": prev,
        "new_split": new,
        "cost_impact": cost_impact,
        "delta_trucks": delta_str,
        "confidence": state.get("confidence", 0.78),
        "deviation": deviation,
        "is_emergency": True,
        "timestamp": _now_iso(),
    }
