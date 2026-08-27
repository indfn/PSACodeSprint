"""PORTNET — Community Data endpoint (wraps feeder data with community context)."""

from fastapi import APIRouter
from app.mocks.data import get_feeder_data

router = APIRouter(prefix="/api/portnet", tags=["PORTNET"])


@router.get("/feeder/{feeder_id}")
async def get_feeder_status(feeder_id: str):
    """PORTNET view of feeder status — wraps feeder data with community sync context."""
    data = get_feeder_data(feeder_id)
    data["portnet_source"] = "community_sync"
    return data


@router.get("/feeders")
async def list_feeders():
    """List available feeders."""
    data = get_feeder_data("FEEDER ATLANTIC-03")
    return {"status": "success", "count": 1, "feeders": [data]}


@router.post("/sea-itt/capacity")
async def sea_itt_capacity(body: dict | None = None):
    """POST sea ITT capacity for compatibility."""
    feeder_id = (body or {}).get("feeder_id", "FEEDER ATLANTIC-03")
    return get_feeder_data(feeder_id)
