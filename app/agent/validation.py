"""Input validation guardrails — charter §4 six guards (Phase 6.8)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def _parse_dt(s: str | None) -> datetime | None:
    if not isinstance(s, str) or not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


# Guardrails as (name, check_fn, action_on_failure)
GUARDRAILS: list[tuple[str, Any, str]] = []


def _guard_weight_bounds(state: dict[str, Any]) -> tuple[bool, str]:
    """Guard: weight_bounds — each container 0 < weight < 60000 kg."""
    context = state.get("context", {}) or {}
    candidates = context.get("candidates")
    if not candidates or not isinstance(candidates, dict):
        # Also check if event contains containers directly?
        return True, ""
    containers = candidates.get("containers")
    if not isinstance(containers, list):
        return True, ""
    failed = []
    for c in containers:
        w = c.get("weight_kg")
        if w is None or not isinstance(w, (int, float)) or w <= 0 or w >= 60000:
            failed.append(c.get("container_id", "?"))
    if failed:
        return False, f"weight_bounds failed for containers: {failed[:5]}"
    return True, ""


def _guard_block_capacity(state: dict[str, Any]) -> tuple[bool, str]:
    context = state.get("context", {}) or {}
    candidates = context.get("candidates")
    block_max = 4500
    # try cost_params
    try:
        from app.configs.problem_config import load_problem_config
        from app.agent.problem_switcher import get_active_problem_id
        cfg = load_problem_config(get_active_problem_id())
        block_max = int((cfg.cost_params or {}).get("block_max_capacity_teu", 4500))
    except Exception:
        pass
    # explicit override
    constraints = context.get("constraints", {}) or {}
    if isinstance(constraints, dict) and "block_max_capacity_teu" in constraints:
        try:
            block_max = int(constraints["block_max_capacity_teu"])
        except Exception:
            pass

    if candidates and isinstance(candidates, dict):
        total_teu = candidates.get("total_teu")
        if total_teu is None and "containers" in candidates:
            containers = candidates.get("containers", [])
            teu = 0
            for c in containers:
                if c.get("size") == "40ft":
                    teu += 2
                elif c.get("size") == "20ft":
                    teu += 1
            total_teu = teu
        if total_teu is not None:
            blocks = candidates.get("blocks_affected", [])
            n_blocks = len(blocks) if isinstance(blocks, list) and blocks else 4
            per_block = total_teu / n_blocks if n_blocks else total_teu
            if per_block > block_max:
                return False, f"block capacity exceeded: {per_block:.1f} TEU/block > {block_max}"
    return True, ""


def _guard_truck_availability(state: dict[str, Any]) -> tuple[bool, str]:
    context = state.get("context", {}) or {}
    road_capacity = context.get("road_capacity")
    # If no road_capacity yet, cannot validate — pass
    if not road_capacity:
        return True, ""
    if isinstance(road_capacity, dict):
        avail = road_capacity.get("available_trucks")
        if isinstance(avail, int) and avail < 1:
            return False, "truck availability guard: no trucks available — fall back to 100% sea"
    return True, ""


def _guard_feeder_capacity(state: dict[str, Any]) -> tuple[bool, str]:
    context = state.get("context", {}) or {}
    sea_capacity = context.get("sea_capacity")
    split_result = context.get("split_result")
    if not sea_capacity or not split_result:
        return True, ""
    if isinstance(sea_capacity, dict) and isinstance(split_result, dict):
        avail = sea_capacity.get("available_capacity_teu")
        if avail is None and "capacity_teu" in sea_capacity and "current_occupancy_teu" in sea_capacity:
            try:
                avail = int(sea_capacity["capacity_teu"]) - int(sea_capacity["current_occupancy_teu"])
            except Exception:
                avail = None
        sea_needed = split_result.get("sea_containers")
        if isinstance(avail, int) and isinstance(sea_needed, int) and sea_needed > avail:
            return False, f"feeder capacity guard: sea_containers {sea_needed} > available {avail}"
    return True, ""


def _guard_vessel_margin(state: dict[str, Any]) -> tuple[bool, str]:
    context = state.get("context", {}) or {}
    # vessel departure vs ITT arrival
    tuas_departure = context.get("tuas_vessel_departure") or context.get("vessel_departure")
    # timeline may hold arrival
    timeline = context.get("timeline") or {}
    # also split_result timeline? use context directly
    itt_arrival = None
    if isinstance(timeline, dict):
        itt_arrival = timeline.get("sea_itt_arrival") or timeline.get("sea_arrival")
    if not itt_arrival and isinstance(context.get("split_result"), dict):
        # optimiser timeline stored separately? check context["timeline"]
        pass
    # Prefer explicit ITT arrival from context
    if not tuas_departure:
        return True, ""
    vd = _parse_dt(str(tuas_departure))
    # If no arrival yet, assume 60 min margin check deferred
    if itt_arrival:
        ia = _parse_dt(str(itt_arrival))
        if vd and ia:
            if not (ia < (vd - timedelta(minutes=60))):
                return False, f"vessel margin guard: ITT arrival {ia} not < departure {vd} -60m"
    return True, ""


def _guard_tidal_window(state: dict[str, Any]) -> tuple[bool, str]:
    context = state.get("context", {}) or {}
    sea_capacity = context.get("sea_capacity")
    if not sea_capacity or not isinstance(sea_capacity, dict):
        return True, ""
    dw = sea_capacity.get("departure_window", {})
    dc = sea_capacity.get("downstream_constraints", {})
    feeder_dep = None
    tidal = None
    if isinstance(dw, dict):
        feeder_dep = dw.get("latest") or dw.get("earliest") or dw.get("requested")
    if isinstance(dc, dict):
        tidal = dc.get("tidal_window") or dc.get("must_depart_by")
    # allow overrides via context constraints
    constraints = context.get("constraints", {}) or {}
    if isinstance(constraints, dict):
        if constraints.get("tidal_deadline"):
            tidal = constraints["tidal_deadline"]
        if constraints.get("feeder_departure"):
            feeder_dep = constraints["feeder_departure"]
    fd = _parse_dt(str(feeder_dep)) if feeder_dep else None
    td = _parse_dt(str(tidal)) if tidal else None
    if fd and td:
        if not (fd < td):
            return False, f"tidal window guard: feeder {fd} not < tidal {td}"
    return True, ""


GUARD_CHECKS = [
    ("weight_bounds", _guard_weight_bounds, "Reject container, log warning"),
    ("block_capacity", _guard_block_capacity, "Trigger overflow routing"),
    ("truck_availability", _guard_truck_availability, "Fall back to 100% sea ITT"),
    ("feeder_capacity", _guard_feeder_capacity, "Reduce sea allocation"),
    ("vessel_margin", _guard_vessel_margin, "Reject split — insufficient margin"),
    ("tidal_window", _guard_tidal_window, "Enforce hold limit in split"),
]


def validate_all(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Run all 6 guardrails.

    Returns list of failures (empty if all passed). Each failure is dict
    with guard name, error, action.
    """
    from app.shared.logging import structured_log

    failures: list[dict[str, Any]] = []
    for name, check, action in GUARD_CHECKS:
        try:
            ok, err = check(state)
        except Exception as exc:
            ok, err = False, f"guard {name} exception: {exc}"
        if not ok:
            failures.append({"guard": name, "error": err, "action": action})
            try:
                structured_log(
                    "guardrail_failed",
                    run_id=state.get("run_id", ""),
                    step=name,
                    guard=name,
                    error=err,
                    action=action,
                )
            except Exception:
                pass
    return failures


def validate_split_modification(modifications: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Validate a MODIFY request's adjusted split against guardrails."""
    # Build a temporary state with modified split_result
    import copy

    tmp = copy.deepcopy(state)
    ctx = tmp.setdefault("context", {})
    # modifications expected: {"road_containers": 100, "sea_containers": 20} etc.
    if modifications:
        # Create a pseudo split_result for validation
        existing = ctx.get("split_result", {}) or {}
        merged = dict(existing)
        merged.update(modifications)
        # Ensure road_trips computed if needed
        if "road_trips" not in merged and "road_containers" in merged:
            # Rough: 40x40ft + remainder 20ft
            rc = merged.get("road_containers", 0)
            # Assume 40 FEU fixed
            if rc >= 40:
                teu20 = rc - 40
                merged["road_trips"] = 40 + (teu20 // 2)
            else:
                merged["road_trips"] = rc  # fallback
        ctx["split_result"] = merged

    failures = validate_all(tmp)
    if failures:
        return {"valid": False, "error": "; ".join(f["error"] for f in failures), "failures": failures}
    return {"valid": True, "failures": []}
