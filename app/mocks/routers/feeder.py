"""Feeder — Sea ITT Capacity endpoint (Tool 3)."""

from fastapi import APIRouter
from app.mocks.data import get_feeder_data

router = APIRouter(prefix="/api/feeder", tags=["Feeder"])


@router.get("/{feeder_id}")
async def check_sea_itt_capacity(feeder_id: str):
    """Query PORTNET for feeder vessel availability, berth status, and departure window."""
    return get_feeder_data(feeder_id)
