"""CITOS PPT — Container Readiness endpoint (Tool 1)."""

from fastapi import APIRouter, Query
from prototype.mocks.data import get_container_data

router = APIRouter(prefix="/api/citos/ppt", tags=["CITOS PPT"])


@router.get("/containers")
async def get_itt_candidates(
    vessel_id: str = Query(default="MV PACIFIC STAR", description="Vessel ID"),
):
    """Query PPT CITOS for containers requiring cross-terminal transfer to Tuas."""
    return get_container_data(vessel_id)
