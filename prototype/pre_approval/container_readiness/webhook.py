"""
T6: receive_webhook — Container Readiness Event Receiver

Receives ITT_COORDINATION_REQUEST events from PPT CITOS via webhook.
This is the agent entry point (Tool 6 in Master Charter §3).

Called by CITOS (PPT) when containers are ready for cross-terminal
transfer to Tuas Port. Validates payload, bootstraps initial agent state,
and triggers the LangGraph agent.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

SGT = timezone(timedelta(hours=8))

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "container_readiness.yaml"

def _load_config() -> dict:
    """Load config from YAML, falling back to defaults if file is missing."""
    defaults = {"min_container_count": 50}
    try:
        with open(_CONFIG_PATH) as f:
            config = yaml.safe_load(f) or {}
        defaults.update(config)
    except FileNotFoundError:
        logging.warning("Config not found at %s, using defaults", _CONFIG_PATH)
    return defaults

_CONFIG = _load_config()
MIN_CONTAINER_COUNT: int = _CONFIG["min_container_count"]


# ---------------------------------------------------------------------------
# Pydantic model — webhook payload schema
# ---------------------------------------------------------------------------
class ITTCoordinationEvent(BaseModel):
    """Payload sent by PPT CITOS when containers are ready for ITT."""

    event_type: str = Field(
        ..., description="Event identifier", examples=["ITT_COORDINATION_REQUEST"]
    )
    timestamp: str = Field(..., description="ISO 8601 event timestamp")
    source: str = Field(
        ..., description="System that raised the event", examples=["CITOS_PPT"]
    )
    priority: str = Field(
        ..., description="Priority level", examples=["high", "critical"]
    )
    origin_terminal: str = Field(
        ..., description="Origin terminal code", examples=["PPT"]
    )
    destination_terminal: str = Field(
        ..., description="Destination terminal code", examples=["TUAS"]
    )
    vessel_id: str = Field(
        ..., description="Mother vessel identifier", examples=["MV PACIFIC STAR"]
    )
    tuas_vessel_departure: str = Field(
        ..., description="ISO 8601 — vessel departure at Tuas"
    )
    container_count: int = Field(
        ..., ge=1, description="Total containers requiring ITT"
    )
    containers_ready: int = Field(
        ..., ge=0, description="Containers confirmed ready now"
    )
    blocks_affected: list[str] = Field(
        ..., description="Yard blocks containing ready containers"
    )
    dg_containers: int = Field(
        0, ge=0, description="Dangerous goods containers in batch"
    )
    priority_containers: int = Field(
        0, ge=0, description="Priority/high-value containers in batch"
    )
    requested_by: str = Field(
        ..., description="Human identifier of the requester"
    )
    notes: str = Field("", description="Optional free-text context")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def validate_event(event: ITTCoordinationEvent) -> list[str]:
    """Return a list of validation error messages (empty = valid)."""
    errors: list[str] = []

    if event.container_count < MIN_CONTAINER_COUNT:
        errors.append(
            f"container_count must be >= {MIN_CONTAINER_COUNT} for ITT coordination "
            f"(got {event.container_count})"
        )

    now = datetime.now(SGT)
    try:
        departure = datetime.fromisoformat(event.tuas_vessel_departure)
        if departure.tzinfo is None:
            departure = departure.replace(tzinfo=SGT)
        if departure < now + timedelta(hours=2):
            errors.append(
                "tuas_vessel_departure must be > 2 hours from now "
                f"(got {event.tuas_vessel_departure})"
            )
    except ValueError:
        errors.append(
            f"tuas_vessel_departure is not valid ISO 8601: "
            f"{event.tuas_vessel_departure}"
        )

    if event.containers_ready > event.container_count:
        errors.append(
            f"containers_ready ({event.containers_ready}) cannot exceed "
            f"container_count ({event.container_count})"
        )

    return errors


# ---------------------------------------------------------------------------
# Initial agent state bootstrap
# ---------------------------------------------------------------------------
def bootstrap_agent_state(event: ITTCoordinationEvent, run_id: str) -> dict:
    """Create the initial LangGraph agent state from the webhook payload."""
    return {
        "run_id": run_id,
        "event": event.model_dump(),
        "origin_terminal": event.origin_terminal,
        "destination_terminal": event.destination_terminal,
        "vessel_id": event.vessel_id,
        "container_count": event.container_count,
        "containers_ready": event.containers_ready,
        "tuas_vessel_departure": event.tuas_vessel_departure,
        "blocks_affected": event.blocks_affected,
        "dg_containers": event.dg_containers,
        "priority_containers": event.priority_containers,
        "requested_by": event.requested_by,
        "priority": event.priority,
        "current_step": "ingest",
        "hitl_pending": [],
        "escalations": [],
        "confidence_scores": [],
        "deviation_log": [],
    }


# ---------------------------------------------------------------------------
# Webhook endpoint — T6
# ---------------------------------------------------------------------------
@router.post("/webhook/itt-coordination")
async def receive_container_readiness(event: ITTCoordinationEvent) -> dict:
    """
    **T6 — Container Readiness Event Receiver**

    Webhook endpoint for ``ITT_COORDINATION_REQUEST`` events.

    Called by CITOS (PPT) when containers are ready for cross-terminal
    transfer.  Validates the payload, creates the initial agent state, and
    triggers the LangGraph agent.

    Returns:
        ``{"status": "accepted", "run_id": "<uuid>"}``
    """
    errors = validate_event(event)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    run_id = f"run-{uuid.uuid4().hex[:12]}"

    # --- Agent trigger (mock) -----------------------------------------------
    # TODO: wire in LangGraph agent
    #     initial_state = bootstrap_agent_state(event, run_id)
    #     result = await agent_graph.ainvoke(initial_state)
    logger = logging.getLogger("container_readiness.webhook")
    logger.info(
        "T6 webhook accepted | run_id=%s | vessel=%s | containers=%d | "
        "blocks=%s | departure=%s",
        run_id,
        event.vessel_id,
        event.container_count,
        event.blocks_affected,
        event.tuas_vessel_departure,
    )

    return {
        "status": "accepted",
        "run_id": run_id,
        "event_type": event.event_type,
        "origin": event.origin_terminal,
        "destination": event.destination_terminal,
        "vessel_id": event.vessel_id,
        "container_count": event.container_count,
    }


# ---------------------------------------------------------------------------
# Sample payload — for manual testing / demo triggers
# ---------------------------------------------------------------------------
def _sample_payload() -> dict:
    """Generate a fresh sample payload with a valid future departure time."""
    return {
        "event_type": "ITT_COORDINATION_REQUEST",
        "timestamp": "2026-08-19T10:30:00+08:00",
        "source": "CITOS_PPT",
        "priority": "high",
        "origin_terminal": "PPT",
        "destination_terminal": "TUAS",
        "vessel_id": "MV PACIFIC STAR",
        "tuas_vessel_departure": (datetime.now(SGT) + timedelta(hours=6)).isoformat(),
        "container_count": 120,
        "containers_ready": 120,
        "blocks_affected": ["B-07", "B-08", "B-12", "B-14"],
        "dg_containers": 3,
        "priority_containers": 45,
        "requested_by": "PPT_Yard_Planner_Lim",
        "notes": (
            "Priority transhipment for MV PACIFIC STAR. "
            "120 containers ready for cross-terminal ITT."
        ),
    }
