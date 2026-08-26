"""FastAPI router for Sea ITT mock endpoints.

Provides:
- POST /portnet/sea-itt/capacity    — Tool 3: Query feeder vessel capacity & tidal constraints
- GET  /portnet/feeder/{feeder_id}  — Lightweight feeder status check (monitoring)
- POST /portnet/feeder/hold         — Request feeder hold at berth
- GET  /portnet/feeders             — List all available feeders
- GET  /portnet/downstream/{port}   — Query downstream port tidal window
- POST /portnet/sea-itt/conflict    — Edge case: simulate berth conflict
"""

from fastapi import APIRouter
from datetime import datetime, timedelta

from .models import (
    SeaITTCapacityRequest,
    FeederHoldRequest,
    FeederHoldResponse,
    FeederStatusResponse,
)
from .data_access import (
    FEEDER_FLEET,
    get_feeder_status,
    get_available_feeders,
    get_downstream_port_info,
    get_feeder_hold_cost,
    simulate_berth_conflict,
)
from .sea_itt_tools import check_sea_itt_capacity

router = APIRouter(prefix="/portnet", tags=["PORTNET Sea ITT"])


@router.post("/sea-itt/capacity")
async def query_sea_itt_capacity(request: SeaITTCapacityRequest):
    """Tool 3: Query PORTNET for feeder vessel capacity and downstream constraints.

    Returns feeder availability, berth status, departure window, tidal feasibility,
    and cost parameters. Matches Master Charter §3 Tool 3 schema.
    """
    result = check_sea_itt_capacity(
        portnet_endpoint=request.portnet_endpoint,
        feeder_id=request.feeder_id,
        current_time=request.current_time,
    )
    return result


@router.get("/feeder/{feeder_id}", response_model=FeederStatusResponse)
async def get_feeder_status_endpoint(feeder_id: str):
    """Lightweight feeder status check — for monitoring and edge case detection.

    Returns berth status, departure status, and delay information.
    Used by agent to continuously monitor feeder during execution.
    """
    feeder = get_feeder_status(feeder_id)
    if not feeder:
        return {"status": "error", "error": f"Feeder '{feeder_id}' not found"}

    return {
        "status": "success",
        "feeder_id": feeder_id,
        "berth_status": feeder["berth_status"],
        "departure_status": "on_schedule",
        "delay_minutes": 0,
        "berth_conflict": False,
        "data_timestamp": datetime.now().isoformat(),
    }


@router.post("/feeder/hold", response_model=FeederHoldResponse)
async def request_feeder_hold(request: FeederHoldRequest):
    """Request to hold a feeder vessel at berth.

    Computes cost and tidal risk of the hold. Returns assessment for
    HITL Gate 3 approval card.
    """
    result = get_feeder_hold_cost(
        feeder_id=request.feeder_id,
        hold_hours=request.hold_hours,
    )
    return result


@router.get("/feeders")
async def list_available_feeders():
    """List all feeders currently available for ITT loading.

    Returns feeders that are berthed at PPT with available capacity.
    """
    feeders = get_available_feeders()
    return {
        "status": "success",
        "count": len(feeders),
        "feeders": [
            {
                "feeder_id": f["feeder_id"],
                "operator": f["feeder_operator"],
                "available_teu": f["available_capacity_teu"],
                "berth_status": f["berth_status"],
                "destination": f["downstream_constraints"]["destination_port"],
            }
            for f in feeders
        ],
    }


@router.get("/downstream/{port_name}")
async def query_downstream_port(port_name: str):
    """Query downstream port tidal window and transit information.

    Returns tidal window schedule, transit time, draft limits, and pilot status.
    """
    info = get_downstream_port_info(port_name)
    return {"status": "success", **info}


@router.post("/sea-itt/conflict")
async def inject_berth_conflict(
    feeder_id: str = "FEEDER ATLANTIC-03",
    delay_minutes: int = 120,
):
    """Edge case: Simulate a berth conflict for the specified feeder.

    Injected at Step 8 of the demo (Master Charter §7 Scenario A).
    Returns updated feeder status with delayed departure.
    """
    conflict = simulate_berth_conflict(feeder_id)
    if "error" in conflict:
        return conflict

    # Override delay if specified
    if delay_minutes != 120:
        conflict["delay_minutes"] = delay_minutes
        # Recalculate new departure window
        dep_original = datetime.fromisoformat(
            FEEDER_FLEET[feeder_id]["departure_window"]["earliest"]
        )
        dep_delayed = dep_original + timedelta(minutes=delay_minutes)
        conflict["new_departure_window"] = {
            "earliest": dep_delayed.isoformat(),
            "latest": (dep_delayed + timedelta(hours=2)).isoformat(),
        }

    return {
        "status": "success",
        "message": f"Berth conflict injected for {feeder_id}",
        **conflict,
    }
