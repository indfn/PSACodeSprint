"""Webhook endpoint — receives ITT_COORDINATION_REQUEST events (T6 trigger)."""

import uuid
from collections import OrderedDict
from fastapi import APIRouter, HTTPException
from prototype.mocks.schemas import ITTCoordinationEvent, WebhookResponse

router = APIRouter(prefix="/webhook", tags=["Webhook"])

MAX_RUNS = 100
runs: OrderedDict[str, dict] = OrderedDict()


@router.post("/itt-coordination")
async def receive_webhook(event: ITTCoordinationEvent):
    """
    Webhook endpoint for ITT_COORDINATION_REQUEST events.
    Called by CITOS (PPT) when 50+ containers are ready for cross-terminal transfer.
    Validates payload, creates initial agent state, returns accepted status.
    """
    if event.containers_ready > event.container_count:
        raise HTTPException(
            status_code=400,
            detail=f"containers_ready ({event.containers_ready}) cannot exceed container_count ({event.container_count})",
        )

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    runs[run_id] = {
        "run_id": run_id,
        "event": event.model_dump(),
        "status": "accepted",
        "current_step": "ingest",
        "origin_terminal": event.origin_terminal,
        "destination_terminal": event.destination_terminal,
        "vessel_id": event.vessel_id,
        "container_count": event.container_count,
        "tuas_vessel_departure": event.tuas_vessel_departure,
        "blocks_affected": event.blocks_affected,
        "dg_containers": event.dg_containers,
        "hitl_pending": [],
        "escalations": [],
        "confidence_scores": [],
        "deviation_log": [],
    }

    if len(runs) > MAX_RUNS:
        runs.popitem(last=False)

    return WebhookResponse(status="accepted", run_id=run_id)


@router.get("/runs/{run_id}")
async def get_run_status(run_id: str):
    """Get current status of a webhook-triggered run."""
    if run_id not in runs:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return runs[run_id]
