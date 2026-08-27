from fastapi import APIRouter

from app.mocks.pb01_data import get_vessel_data, log_vessel_notification

router = APIRouter(prefix="/api/vtis", tags=["VTIS"])


@router.get("/vessel/{vessel_id}")
async def get_vessel_arrival(vessel_id: str):
    return get_vessel_data(vessel_id)


@router.post("/notify")
async def notify_vessel(body: dict):
    vessel_id = body.get("vessel_id", "MV EVER GIVEN")
    message = body.get("message", "")
    entry = log_vessel_notification(vessel_id, message)
    return {"notified": vessel_id, "message": message, "timestamp": entry["timestamp"], "status": "sent"}


@router.get("/health")
async def health():
    return {"status": "ok", "service": "vtis-mock"}
