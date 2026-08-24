"""CITOS Tuas — Loading Sequence endpoint (Tool 5)."""

from fastapi import APIRouter, Body
from prototype.mocks.data import get_loading_sequence_data

router = APIRouter(prefix="/api/citos/tuas", tags=["CITOS Tuas"])


@router.post("/loading-sequence")
async def update_tuas_loading_sequence(
    vessel_id: str = Body(...),
    itt_eta_road: str = Body(...),
    itt_eta_sea: str = Body(...),
    container_ids_road: list[str] = Body(default=[]),
    container_ids_sea: list[str] = Body(default=[]),
):
    """Update Tuas QC loading sequence based on ITT arrival predictions."""
    return get_loading_sequence_data(vessel_id, itt_eta_road, itt_eta_sea)
