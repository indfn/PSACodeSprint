from fastapi import APIRouter

from app.mocks.pb01_data import get_berth_data

router = APIRouter(prefix="/api/optevoyage", tags=["OptEVoyage"])


@router.get("/berth/{berth_id}")
async def get_berth_availability(berth_id: str, vessel_id: str = "MV EVER GIVEN"):
    return get_berth_data(vessel_id, berth_id)


@router.get("/health")
async def health():
    return {"status": "ok", "service": "optevoyage-mock"}
