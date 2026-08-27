"""CITOS PPT — Container Readiness endpoint (Tool 1). Consolidated mock router."""

from fastapi import APIRouter, Query
from datetime import datetime
from typing import Any

from app.mocks.data import get_container_data

router = APIRouter(prefix="/api/citos/ppt", tags=["CITOS PPT"])


@router.get("/containers")
async def get_itt_candidates(
    vessel_id: str = Query(default="MV PACIFIC STAR", description="Vessel ID"),
):
    """Query PPT CITOS for containers requiring cross-terminal transfer to Tuas."""
    return get_container_data(vessel_id)


@router.post("/itt-candidates")
async def query_itt_candidates_post(body: dict[str, Any] | None = None):
    """POST variant for compatibility with pre_approval router."""
    vessel_id = (body or {}).get("vessel_id", "MV PACIFIC STAR")
    return get_container_data(vessel_id)


@router.get("/yard-status")
async def query_yard_status():
    """Yard block occupancy status."""
    return {
        "status": "success",
        "terminal": "PPT",
        "blocks": {
            "B-07": {"occupancy": 0.85, "available": False},
            "B-08": {"occupancy": 0.72, "available": True},
            "B-12": {"occupancy": 0.90, "available": False},
            "B-14": {"occupancy": 0.65, "available": True},
        },
        "last_updated": datetime.now().isoformat(),
        "data_age_minutes": 0.5,
    }


@router.post("/itt-candidates-stale")
async def query_stale(body: dict[str, Any] | None = None, age_minutes: float = 25.0):
    """Edge case: stale data simulation."""
    vessel_id = (body or {}).get("vessel_id", "MV PACIFIC STAR") if body else "MV PACIFIC STAR"
    data = get_container_data(vessel_id)
    data["data_timestamp"] = datetime.now().isoformat()
    data["data_age_minutes"] = age_minutes
    data["edge_case"] = "data_staleness"
    return data
