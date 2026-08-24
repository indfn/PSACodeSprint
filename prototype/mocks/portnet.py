"""PORTNET — Community Data endpoint (wraps feeder data with community context)."""

from fastapi import APIRouter
from prototype.mocks.data import get_feeder_data

router = APIRouter(prefix="/api/portnet", tags=["PORTNET"])


@router.get("/feeder/{feeder_id}")
async def get_feeder_status(feeder_id: str):
    """PORTNET view of feeder status — wraps feeder data with community sync context."""
    data = get_feeder_data(feeder_id)
    data["portnet_source"] = "community_sync"
    return data
