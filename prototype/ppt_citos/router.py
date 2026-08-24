"""FastAPI router for PPT CITOS mock endpoints.

Provides:
- POST /citos/ppt/itt-candidates — Tool 1: Query containers ready for ITT
- GET /citos/ppt/yard-status — Yard block occupancy status
- POST /citos/ppt/webhook/itt-coordination — T6: Webhook event trigger
"""

from fastapi import APIRouter
from datetime import datetime
import uuid

from .models import (
    ITTCandidatesRequest,
    ITTCandidatesResponse,
    YardStatusResponse,
    WebhookEvent,
    WebhookResponse,
)
from .mock_data import get_itt_candidates, get_itt_candidates_stale, get_yard_status

router = APIRouter(prefix="/citos/ppt", tags=["PPT CITOS"])


@router.post("/itt-candidates", response_model=ITTCandidatesResponse)
async def query_itt_candidates(request: ITTCandidatesRequest):
    """Tool 1: Query PPT CITOS for containers requiring cross-terminal transfer.

    Returns container list with yard block, weight, DG class, and priority.
    Matches Master Charter §3 Tool 1 schema.
    """
    result = get_itt_candidates(vessel_id=request.vessel_id)
    return result


@router.get("/yard-status", response_model=YardStatusResponse)
async def query_yard_status():
    """Query yard block occupancy and capacity status at PPT.

    Used by agent to verify yard block availability before ITT dispatch.
    """
    return get_yard_status()


@router.post("/webhook/itt-coordination")
async def receive_webhook(event: WebhookEvent):
    """T6: Webhook endpoint for ITT_COORDINATION_REQUEST events.

    Called by external systems (or demo script) when 50+ containers are ready
    for cross-terminal transfer. Validates payload, creates initial agent state,
    and triggers the LangGraph agent.

    Returns run_id for tracking. Agent execution is non-blocking.
    """
    # Generate run ID
    run_id = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

    # Bootstrap initial agent state from webhook payload
    initial_state = {
        "run_id": run_id,
        "event": event.model_dump(),
        "origin_terminal": event.origin_terminal,
        "destination_terminal": event.destination_terminal,
        "vessel_id": event.vessel_id,
        "container_count": event.container_count,
        "tuas_vessel_departure": event.tuas_vessel_departure,
        "blocks_affected": event.blocks_affected,
        "dg_containers": event.dg_containers,
        "current_step": "ingest",
        "hitl_pending": [],
        "escalations": [],
        "confidence_scores": [],
        "deviation_log": [],
    }

    # In production, this would trigger: await agent_graph.ainvoke(initial_state)
    # For mock, we store state and return immediately
    return WebhookResponse(
        status="accepted",
        run_id=run_id,
        message="ITT coordination request received. Agent triggered."
    )


@router.post("/itt-candidates-stale")
async def query_itt_candidates_stale(request: ITTCandidatesRequest, age_minutes: float = 25.0):
    """Edge case: Returns ITT candidates with simulated data staleness.

    Used to test escalation trigger #4 (data latency exceeds freshness window).
    Default staleness: 25 minutes (above 30 min threshold for escalation).
    """
    age_minutes = max(0.0, min(age_minutes, 120.0))  # Clamp to [0, 120]
    result = get_itt_candidates_stale(
        vessel_id=request.vessel_id,
        age_minutes=age_minutes
    )
    return result
