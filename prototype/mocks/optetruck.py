"""OptETruck — Road ITT Capacity endpoint (Tool 2)."""

from fastapi import APIRouter
from prototype.mocks.data import get_truck_data

router = APIRouter(prefix="/api/optetruck", tags=["OptETruck"])


@router.get("/capacity")
async def check_road_itt_capacity():
    """Query OptETruck for available trucks, transit time, and road conditions."""
    return get_truck_data()
