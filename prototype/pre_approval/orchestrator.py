"""
Pre-Approval ITT Pipeline Orchestrator

Coordinates the pre-approval flow:
  1. container_readiness (T6) — receive & validate webhook
  2. Parallel: ppt_citos (T1) + road_itt (T2) + sea_itt (T3)
  3. ai_optimisation (T4) — compute optimal road/sea split
  4. Return raw split result

No LLM, no framework — just async Python.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from .container_readiness import ITTCoordinationEvent, receive_container_readiness
from .ppt_citos import get_itt_candidates
from .road_itt import check_road_itt_capacity
from .sea_itt import check_sea_itt_capacity
from .ai_optimisation import compute_optimal_split

logger = logging.getLogger(__name__)

SGT = timezone(timedelta(hours=8))


# ---------------------------------------------------------------------------
# Pipeline result
# ---------------------------------------------------------------------------

class PreApprovalResult:
    """Final output of the pre-approval pipeline."""

    def __init__(
        self,
        run_id: str,
        event: dict[str, Any],
        agent_state: dict[str, Any],
        split_result: dict[str, Any],
    ):
        self.run_id = run_id
        self.event = event
        self.agent_state = agent_state
        self.split_result = split_result

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "event": self.event,
            "agent_state": self.agent_state,
            "split_result": self.split_result,
        }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def run_pre_approval_pipeline(
    event: ITTCoordinationEvent,
) -> PreApprovalResult:
    """Execute the full pre-approval pipeline.

    Flow:
        T6 (validate) → [T1 ‖ T2 ‖ T3] → T4 (optimise) → return

    Args:
        event: Validated webhook payload from PPT CITOS.

    Returns:
        PreApprovalResult with raw split data.

    Raises:
        ValueError: If webhook validation fails.
    """
    # Step 1: validate & bootstrap via container_readiness webhook
    response = await receive_container_readiness(event)
    run_id = response["run_id"]
    agent_state = response

    # Step 2: parallel data gathering
    candidates, road_capacity, sea_capacity = await _gather_parallel(agent_state)

    # Step 3: optimisation
    split_result = _run_optimisation(
        agent_state, candidates, road_capacity, sea_capacity,
    )

    # Step 4: assemble result
    result = PreApprovalResult(
        run_id=run_id,
        event=event.model_dump(),
        agent_state=agent_state,
        split_result=split_result,
    )

    logger.info(
        "Pipeline complete | run_id=%s | optimal=%s | confidence=%s",
        run_id,
        split_result.get("optimal_split"),
        split_result.get("confidence"),
    )

    return result


# ---------------------------------------------------------------------------
# Step 2: Parallel data gathering (T1 + T2 + T3)
# ---------------------------------------------------------------------------

def _gather_t1(agent_state: dict[str, Any]) -> dict[str, Any]:
    """T1: Query PPT CITOS for ITT candidates."""
    result = get_itt_candidates(vessel_id=agent_state["vessel_id"])
    logger.info(
        "T1 ppt_citos: %d containers (%dx 40ft + %dx 20ft)",
        result["total_containers"],
        result["container_breakdown"]["40ft_feu"],
        result["container_breakdown"]["20ft_teu"],
    )
    return result


def _gather_t2(agent_state: dict[str, Any]) -> dict[str, Any]:
    """T2: Query OptETruck for road ITT capacity."""
    now = datetime.now(SGT)
    departure = datetime.fromisoformat(agent_state["tuas_vessel_departure"])
    if departure.tzinfo is None:
        departure = departure.replace(tzinfo=SGT)

    result = check_road_itt_capacity(
        optetruck_endpoint="http://mocks:8002/api/v1",
        terminal=agent_state["origin_terminal"],
        time_window_start=now.isoformat(),
        time_window_end=departure.isoformat(),
    )
    logger.info(
        "T2 road_itt: trucks=%s, transit=%sm",
        result.get("available_trucks"),
        result.get("transit_time_minutes"),
    )
    return result


def _gather_t3(agent_state: dict[str, Any]) -> dict[str, Any]:
    """T3: Query PORTNET for sea ITT capacity."""
    now = datetime.now(SGT).isoformat()
    result = check_sea_itt_capacity(
        portnet_endpoint="http://mocks:8005/api/v1",
        feeder_id="FEEDER ATLANTIC-03",
        current_time=now,
    )
    logger.info(
        "T3 sea_itt: feeder=%s, available=%s TEU",
        result.get("feeder_id"),
        result.get("available_capacity_teu"),
    )
    return result


async def _gather_parallel(agent_state: dict[str, Any]) -> tuple[dict, dict, dict]:
    """Run T1, T2, T3 concurrently via thread pool (sync functions)."""
    loop = asyncio.get_running_loop()

    t1_task = loop.run_in_executor(None, _gather_t1, agent_state)
    t2_task = loop.run_in_executor(None, _gather_t2, agent_state)
    t3_task = loop.run_in_executor(None, _gather_t3, agent_state)

    candidates_result, road_result, sea_result = await asyncio.gather(
        t1_task, t2_task, t3_task,
    )

    return candidates_result, road_result, sea_result


# ---------------------------------------------------------------------------
# Step 3: Optimisation (T4)
# ---------------------------------------------------------------------------

def _run_optimisation(
    agent_state: dict[str, Any],
    candidates: dict[str, Any],
    road_capacity: dict[str, Any],
    sea_capacity: dict[str, Any],
) -> dict[str, Any]:
    """T4: Compute optimal road/sea split."""
    result = compute_optimal_split(
        problem_id="PB-12",
        candidates=candidates.get("containers"),
        road_capacity=road_capacity,
        sea_capacity=sea_capacity,
        tuas_vessel_departure=agent_state["tuas_vessel_departure"],
    )

    logger.info(
        "T4 optimisation: %d road / %d sea = $%d | confidence=%.2f | %d escalation flags",
        result.get("optimal_split", {}).get("road_containers", "?"),
        result.get("optimal_split", {}).get("sea_containers", "?"),
        result.get("optimal_split", {}).get("total_transport_cost", "?"),
        result.get("confidence", 0),
        len(result.get("escalation_flags", [])),
    )

    return result