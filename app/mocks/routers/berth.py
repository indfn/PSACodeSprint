from fastapi import APIRouter

from app.mocks.pb01_data import get_qc_data

router = APIRouter(prefix="/api/berth", tags=["Berth"])


@router.get("/{berth_id}/qc")
async def get_qc_availability(berth_id: str):
    return get_qc_data(berth_id)


@router.get("/health")
async def health():
    return {"status": "ok", "service": "berth-mock"}
