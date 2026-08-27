"""Canonical Pydantic schemas for PSA Nexus — consolidated from 3 sources.

Sources merged:
  - prototype/mocks/schemas.py (182 lines) — central ITT models
  - prototype/pre_approval/ppt_citos/models.py (79 lines) — PPT-specific
  - prototype/pre_approval/sea_itt/models.py (177 lines) — sea ITT / PORTNET

Canonical location: app/shared/models.py (charter §9 target).
app/mocks must NOT have its own schemas.py — re-export shim only if needed.

Resolves duplicates:
  - Container, ContainerBreakdown, TruckTripRequirement → single definition
  - WebhookEvent / ITTCoordinationEvent → ITTCoordinationEvent (canonical, 15 fields)
  - WebhookResponse → single
  - SeaITTCapacityResponse → unified flat+nested compatible
  - DepartureWindow / FeederDownstreamConstraints → single
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Tool 1: get_itt_candidates (CITOS PPT)
# ---------------------------------------------------------------------------

class Container(BaseModel):
    container_id: str = Field(..., json_schema_extra={"example": "MSKU7654321"})
    size: str = Field(..., json_schema_extra={"example": "40ft"}, pattern=r"^(20ft|40ft)$")
    yard_block: str = Field(..., json_schema_extra={"example": "B-07"})
    yard_position: str = Field(..., json_schema_extra={"example": "Bay 14 Row 02 Tier 03"})
    weight_kg: float = Field(..., gt=0, lt=60000, json_schema_extra={"example": 28500})
    dg_class: Optional[str] = Field(None, json_schema_extra={"example": None})
    priority: str = Field(..., json_schema_extra={"example": "high"}, pattern=r"^(high|standard)$")
    consignee: str = Field(..., json_schema_extra={"example": "DB Schenker"})
    destination_port: str = Field(..., json_schema_extra={"example": "LA"})
    ready_for_itt: bool = Field(True, json_schema_extra={"example": True})


class ContainerBreakdown(BaseModel):
    fortyft_feu: int = Field(..., alias="40ft_feu", json_schema_extra={"example": 40})
    twentyft_teu: int = Field(..., alias="20ft_teu", json_schema_extra={"example": 80})

    model_config = {"populate_by_name": True}


class TruckTripRequirement(BaseModel):
    fortyft_feu_trips: int = Field(..., alias="40ft_feu_trips", json_schema_extra={"example": 40})
    twentyft_teu_trips: int = Field(..., alias="20ft_teu_trips", json_schema_extra={"example": 40})
    total_potential_truck_trips_100pct_road: int = Field(..., json_schema_extra={"example": 80})

    model_config = {"populate_by_name": True}


class ITTCandidatesResponse(BaseModel):
    status: str = Field("success", json_schema_extra={"example": "success"})
    vessel_id: str = Field(..., json_schema_extra={"example": "MV PACIFIC STAR"})
    tuas_departure: str = Field(..., json_schema_extra={"example": "2026-08-19T20:00:00+08:00"})
    total_containers: int = Field(..., json_schema_extra={"example": 120})
    total_teu: int = Field(..., json_schema_extra={"example": 160})
    container_breakdown: ContainerBreakdown
    lta_truck_trip_requirement: TruckTripRequirement
    containers: list[Container]
    blocks_affected: list[str] = Field(..., json_schema_extra={"example": ["B-07", "B-08", "B-12", "B-14"]})
    dg_containers: int = Field(..., json_schema_extra={"example": 3})
    reefer_containers: int = Field(0, json_schema_extra={"example": 0})


class ITTCandidatesRequest(BaseModel):
    """Request model for PPT CITOS Tool 1 (from ppt_citos/models.py)."""

    cit_ppt_endpoint: str = Field(..., json_schema_extra={"example": "CITOS_PPT"})
    vessel_id: str = Field(..., json_schema_extra={"example": "MV PACIFIC STAR"})


class YardStatusResponse(BaseModel):
    """Yard block occupancy status (from ppt_citos/models.py)."""

    status: str = Field("success")
    terminal: str = Field("PPT")
    blocks: dict[str, dict]
    last_updated: str
    data_age_minutes: float


# ---------------------------------------------------------------------------
# Tool 2: check_road_itt_capacity (OptETruck)
# ---------------------------------------------------------------------------

class RoadITTCapacityResponse(BaseModel):
    status: str = Field("success", json_schema_extra={"example": "success"})
    terminal: str = Field("PPT", json_schema_extra={"example": "PPT"})
    available_trucks: int = Field(..., json_schema_extra={"example": 20})
    total_fleet: int = Field(25, json_schema_extra={"example": 25})
    transit_time_minutes: int = Field(..., json_schema_extra={"example": 90})
    road_conditions: dict = Field(..., json_schema_extra={"example": {"AYE": "normal"}, "West_Coast_Highway": "moderate_traffic_near_pandan"})
    cost_per_trip: int = Field(..., json_schema_extra={"example": 150})
    lta_chassis_limits: str = Field(..., json_schema_extra={"example": "1x 40ft/45ft (FEU) OR up to 2x 20ft (TEU) per prime mover"})
    estimated_round_trip_minutes: int = Field(..., json_schema_extra={"example": 210})
    baseline_trips_all_120_containers: int = Field(80, json_schema_extra={"example": 80})
    baseline_road_cost_all_120: int = Field(12000, json_schema_extra={"example": 12000})
    earliest_departure: str = Field(..., json_schema_extra={"example": "2026-08-19T11:00:00+08:00"})
    latest_arrival_at_tuas: str = Field(..., json_schema_extra={"example": "2026-08-19T18:00:00+08:00"})
    capacity_ratio: float = Field(0.25, json_schema_extra={"example": 0.25})


# ---------------------------------------------------------------------------
# Tool 3: check_sea_itt_capacity (PORTNET / Feeder)
# ---------------------------------------------------------------------------

class DepartureWindow(BaseModel):
    earliest: str = Field(..., json_schema_extra={"example": "2026-08-19T14:00:00+08:00"})
    latest: str = Field(..., json_schema_extra={"example": "2026-08-19T16:00:00+08:00"})
    requested: str = Field(..., json_schema_extra={"example": "2026-08-19T14:00:00+08:00"})


class FeederDownstreamConstraints(BaseModel):
    destination_port: str = Field(..., json_schema_extra={"example": "Port Klang"})
    tidal_window: str = Field(..., json_schema_extra={"example": "2026-08-19T23:00:00+08:00"})
    transit_time_hours: float = Field(..., json_schema_extra={"example": 18})
    must_depart_by: str = Field(..., json_schema_extra={"example": "2026-08-19T05:00:00+08:00"})
    buffer_hours: float = Field(1.0, json_schema_extra={"example": 1.0})


# Alias for sea_itt compatibility
DownstreamConstraints = FeederDownstreamConstraints


class FeederCapacity(BaseModel):
    """Feeder vessel capacity (from sea_itt/models.py)."""

    capacity_teu: int = Field(..., json_schema_extra={"example": 800})
    current_occupancy_teu: int = Field(..., json_schema_extra={"example": 620})
    available_capacity_teu: int = Field(..., json_schema_extra={"example": 180})


class SeaITTCapacityResponse(BaseModel):
    """Unified sea ITT capacity — supports both flat and nested representations.

    Flat form (mocks/schemas.py): capacity_teu / current_occupancy_teu / available_capacity_teu
    Nested form (sea_itt/models.py): capacity: FeederCapacity
    Both forms validate; optional fields allow either style.
    """

    status: str = Field("success", json_schema_extra={"example": "success"})
    feeder_id: str = Field(..., json_schema_extra={"example": "FEEDER ATLANTIC-03"})
    feeder_operator: str = Field(..., json_schema_extra={"example": "PIL Shipping"})
    vessel_type: str = Field("Feeder", json_schema_extra={"example": "Feeder"})
    # Flat capacity fields (mocks/schemas)
    capacity_teu: Optional[int] = Field(None, json_schema_extra={"example": 800})
    current_occupancy_teu: Optional[int] = Field(None, json_schema_extra={"example": 620})
    available_capacity_teu: Optional[int] = Field(None, json_schema_extra={"example": 180})
    # Nested capacity (sea_itt/models)
    capacity: Optional[FeederCapacity] = Field(None)
    berth_status: str = Field(..., json_schema_extra={"example": "berthed_at_PPT_B12"})
    departure_window: DepartureWindow
    downstream_constraints: FeederDownstreamConstraints
    hold_cost_per_hour: float = Field(..., json_schema_extra={"example": 800})
    missed_connection_cost: float = Field(..., json_schema_extra={"example": 5000})
    # Optional staleness fields (sea_itt)
    data_timestamp: Optional[str] = Field(None, json_schema_extra={"example": "2026-08-19T10:35:00+08:00"})
    data_age_minutes: Optional[float] = Field(None, json_schema_extra={"example": 0.5})


class SeaITTCapacityRequest(BaseModel):
    """Request to check sea ITT capacity (from sea_itt/models.py)."""

    portnet_endpoint: str = Field(..., json_schema_extra={"example": "PORTNET"})
    feeder_id: str = Field(..., json_schema_extra={"example": "FEEDER ATLANTIC-03"})
    current_time: str = Field(..., json_schema_extra={"example": "2026-08-19T10:35:00+08:00"})


class FeederHoldRequest(BaseModel):
    """Request to hold a feeder vessel at berth."""

    portnet_endpoint: str = Field(..., json_schema_extra={"example": "PORTNET"})
    feeder_id: str = Field(..., json_schema_extra={"example": "FEEDER ATLANTIC-03"})
    hold_hours: float = Field(..., gt=0, le=6, json_schema_extra={"example": 1.0})


class FeederHoldResponse(BaseModel):
    """Response to a feeder hold request."""

    status: str = Field("success")
    feeder_id: str
    hold_hours: float
    hold_cost: float = Field(..., description="Total cost of hold")
    new_departure: str = Field(..., description="Projected new departure time")
    tidal_risk: str = Field(..., description="'safe', 'marginal', or 'critical'")
    message: str = ""


class FeederStatusResponse(BaseModel):
    """Lightweight feeder status check."""

    status: str = Field("success")
    feeder_id: str
    berth_status: str
    departure_status: str = Field(..., json_schema_extra={"example": "on_schedule"})
    delay_minutes: int = Field(0, json_schema_extra={"example": 0})
    berth_conflict: bool = Field(False)
    data_timestamp: str


# ---------------------------------------------------------------------------
# Tool 4: compute_itt_split (internal computation)
# ---------------------------------------------------------------------------

class ITTSplitOption(BaseModel):
    road_containers: int = Field(..., json_schema_extra={"example": 80})
    road_breakdown: str = Field(..., json_schema_extra={"example": "40x 40ft (40 trips) + 40x 20ft (20 trips)"})
    road_trips: int = Field(..., json_schema_extra={"example": 60})
    road_cost: int = Field(..., json_schema_extra={"example": 9000})
    sea_containers: int = Field(..., json_schema_extra={"example": 40})
    sea_marginal_charter_cost: int = Field(0, json_schema_extra={"example": 0})
    sea_terminal_handling_cost: int = Field(..., json_schema_extra={"example": 1400})
    total_transport_cost: int = Field(..., json_schema_extra={"example": 10400})
    cost_notes: str = Field("", json_schema_extra={"example": "Sea transfer has $0 marginal charter cost"})
    risk: Optional[str] = Field(None, json_schema_extra={"example": "road_congestion_delay_near_pandan"})


class ITTSplitTimeline(BaseModel):
    road_itt_arrival: str = Field(..., json_schema_extra={"example": "2026-08-19T14:30:00+08:00"})
    sea_itt_arrival: str = Field(..., json_schema_extra={"example": "2026-08-19T16:30:00+08:00"})
    tuas_loading_start: str = Field(..., json_schema_extra={"example": "2026-08-19T17:00:00+08:00"})
    vessel_departure: str = Field(..., json_schema_extra={"example": "2026-08-19T20:00:00+08:00"})
    margin_minutes: int = Field(180, json_schema_extra={"example": 180})


class ITTSplitResponse(BaseModel):
    status: str = Field("success", json_schema_extra={"example": "success"})
    optimal_split: ITTSplitOption
    alternatives: list[ITTSplitOption]
    timeline: ITTSplitTimeline
    cost_vs_baseline: dict = Field(..., json_schema_extra={"example": {"baseline_all_road_cost": 12000}, "optimised_transport_cost": 10400})


# ---------------------------------------------------------------------------
# Tool 5: update_tuas_loading_sequence (CITOS Tuas)
# ---------------------------------------------------------------------------

class QcAdjustment(BaseModel):
    qc_id: str = Field(..., json_schema_extra={"example": "QC-07"})
    original_bay: str = Field(..., json_schema_extra={"example": "Bay14"})
    new_bay: str = Field(..., json_schema_extra={"example": "Bay14"})
    eta: str = Field(..., json_schema_extra={"example": "14:30"})


class LoadingSequenceResponse(BaseModel):
    status: str = Field("success", json_schema_extra={"example": "success"})
    vessel_id: str = Field(..., json_schema_extra={"example": "MV PACIFIC STAR"})
    original_loading_sequence: str = Field(..., json_schema_extra={"example": "Bay14→Bay12→Bay10→Bay08"})
    updated_loading_sequence: str = Field(..., json_schema_extra={"example": "Bay14(road@14:30)→Bay12(road@14:30)→Bay10(sea@16:30)→Bay08(sea@16:30)"})
    qc_adjustments: list[QcAdjustment]
    estimated_loading_completion: str = Field(..., json_schema_extra={"example": "2026-08-19T19:30:00+08:00"})
    margin_before_departure_minutes: int = Field(30, json_schema_extra={"example": 30})


# ---------------------------------------------------------------------------
# Webhook / Trigger — ITT_COORDINATION_REQUEST event
# Canonical: ITTCoordinationEvent (15 charter fields)
# ---------------------------------------------------------------------------

class ITTCoordinationEvent(BaseModel):
    event_type: str = Field(..., json_schema_extra={"example": "ITT_COORDINATION_REQUEST"})
    timestamp: str = Field(..., json_schema_extra={"example": "2026-08-19T10:30:00+08:00"})
    source: str = Field(..., json_schema_extra={"example": "CITOS_PPT"})
    priority: str = Field(..., json_schema_extra={"example": "high"})
    origin_terminal: str = Field("PPT")
    destination_terminal: str = Field("TUAS")
    vessel_id: str = Field(..., json_schema_extra={"example": "MV PACIFIC STAR"})
    tuas_vessel_departure: str = Field(..., json_schema_extra={"example": "2026-08-19T20:00:00+08:00"})
    container_count: int = Field(..., ge=50, json_schema_extra={"example": 120})
    containers_ready: int = Field(..., json_schema_extra={"example": 120})
    blocks_affected: list[str] = Field(..., json_schema_extra={"example": ["B-07", "B-08", "B-12", "B-14"]})
    dg_containers: int = Field(0, ge=0, json_schema_extra={"example": 3})
    priority_containers: int = Field(0, ge=0, json_schema_extra={"example": 45})
    requested_by: str = Field(..., json_schema_extra={"example": "PPT_Yard_Planner_Lim"})
    notes: str = Field("", json_schema_extra={"example": "Priority transhipment for MV PACIFIC STAR"})


# Alias for backward compatibility (ppt_citos used WebhookEvent)
WebhookEvent = ITTCoordinationEvent


class WebhookResponse(BaseModel):
    status: str = Field("accepted")
    run_id: str
    message: str = "ITT coordination request received. Agent triggered."


# Re-export shim compatibility: allow `from app.mocks.schemas import ...` if ever needed
# (not created as a file, but models are discoverable via app.shared.models)

# ---------------------------------------------------------------------------
# Phase 6 placeholders — forward-declared so imports don't break before Phase 6
# Real definitions: app/agent/state.py (AgentState), app/hitl/models.py (HITL*),
#                   app/agent/trace.py (TraceEntry)
# These are Optional / loose placeholders to avoid circular imports.
# ---------------------------------------------------------------------------

from typing import TypedDict, Literal

class AgentState(TypedDict, total=False):
    """Placeholder for LangGraph state — real definition in app/agent/state.py (Phase 6.1)."""

    messages: list[dict[str, Any]]
    run_id: str
    event: dict[str, Any]
    tool_results: dict[str, Any]
    confidence: float
    hitl_pending: list[dict[str, Any]]
    escalations: list[dict[str, Any]]
    trace: list[dict[str, Any]]
    current_step: str
    problem_id: str
    # Allow any additional keys for forward compatibility
    # (TypedDict total=False permits optional fields)


class HITLGatePlaceholder(BaseModel):
    """Placeholder HITL gate — real definition in app/hitl/models.py (Phase 6.5)."""

    gate_id: str = Field(..., json_schema_extra={"example": "hitl_1"})
    label: str = Field(..., json_schema_extra={"example": "Approve ITT Split"})
    trigger: str = Field(..., json_schema_extra={"example": "split_computed"})
    timeout_minutes: int = Field(30)
    timeout_action: str = Field("escalate_to_duty_manager")
    status: str = Field("pending", json_schema_extra={"example": "pending"})
    payload: dict[str, Any] = Field(default_factory=dict)


# Expose as HITLGate alias for import compatibility — config's HITLGate is separate
# If Phase 6 defines a richer HITLGate, this placeholder will be replaced.
HITLGate = HITLGatePlaceholder  # type: ignore


class HITLDecision(BaseModel):
    """Placeholder HITL decision — real definition in app/hitl/models.py (Phase 6.5)."""

    gate_id: str
    decision: Literal["approve", "reject", "modify"]
    reason: str | None = None
    modifications: dict[str, Any] | None = None
    decided_by: str | None = None
    timestamp: str | None = None


class TraceEntry(BaseModel):
    """Placeholder trace entry — real definition in app/agent/trace.py (Phase 6.8)."""

    timestamp: str
    run_id: str
    step: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float | None = None
