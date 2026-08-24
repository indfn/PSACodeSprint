"""Pydantic models for all 5 PSA mock systems — matches Master Charter §3 tool specs."""

from pydantic import BaseModel, Field
from typing import Optional


# ---------------------------------------------------------------------------
# Tool 1: get_itt_candidates (CITOS PPT)
# ---------------------------------------------------------------------------

class Container(BaseModel):
    container_id: str = Field(..., example="MSKU7654321")
    size: str = Field(..., example="40ft", pattern=r"^(20ft|40ft)$")
    yard_block: str = Field(..., example="B-07")
    yard_position: str = Field(..., example="Bay 14 Row 02 Tier 03")
    weight_kg: float = Field(..., gt=0, lt=60000, example=28500)
    dg_class: Optional[str] = Field(None, example=None)
    priority: str = Field(..., example="high", pattern=r"^(high|standard)$")
    consignee: str = Field(..., example="DB Schenker")
    destination_port: str = Field(..., example="LA")
    ready_for_itt: bool = Field(True, example=True)


class ContainerBreakdown(BaseModel):
    fortyft_feu: int = Field(..., alias="40ft_feu", example=40)
    twentyft_teu: int = Field(..., alias="20ft_teu", example=80)


class TruckTripRequirement(BaseModel):
    fortyft_feu_trips: int = Field(..., alias="40ft_feu_trips", example=40)
    twentyft_teu_trips: int = Field(..., alias="20ft_teu_trips", example=40)
    total_potential_truck_trips_100pct_road: int = Field(..., example=80)


class ITTCandidatesResponse(BaseModel):
    status: str = Field("success", example="success")
    vessel_id: str = Field(..., example="MV PACIFIC STAR")
    tuas_departure: str = Field(..., example="2026-08-19T20:00:00+08:00")
    total_containers: int = Field(..., example=120)
    total_teu: int = Field(..., example=160)
    container_breakdown: ContainerBreakdown
    lta_truck_trip_requirement: TruckTripRequirement
    containers: list[Container]
    blocks_affected: list[str] = Field(..., example=["B-07", "B-08", "B-12", "B-14"])
    dg_containers: int = Field(..., example=3)
    reefer_containers: int = Field(0, example=0)


# ---------------------------------------------------------------------------
# Tool 2: check_road_itt_capacity (OptETruck)
# ---------------------------------------------------------------------------

class RoadITTCapacityResponse(BaseModel):
    status: str = Field("success", example="success")
    terminal: str = Field("PPT", example="PPT")
    available_trucks: int = Field(..., example=20)
    total_fleet: int = Field(25, example=25)
    transit_time_minutes: int = Field(..., example=90)
    road_conditions: dict = Field(..., example={"AYE": "normal", "West_Coast_Highway": "moderate_traffic_near_pandan"})
    cost_per_trip: int = Field(..., example=150)
    lta_chassis_limits: str = Field(..., example="1x 40ft/45ft (FEU) OR up to 2x 20ft (TEU) per prime mover")
    estimated_round_trip_minutes: int = Field(..., example=210)
    baseline_trips_all_120_containers: int = Field(80, example=80)
    baseline_road_cost_all_120: int = Field(12000, example=12000)
    earliest_departure: str = Field(..., example="2026-08-19T11:00:00+08:00")
    latest_arrival_at_tuas: str = Field(..., example="2026-08-19T18:00:00+08:00")
    capacity_ratio: float = Field(0.25, example=0.25)


# ---------------------------------------------------------------------------
# Tool 3: check_sea_itt_capacity (PORTNET / Feeder)
# ---------------------------------------------------------------------------

class FeederDownstreamConstraints(BaseModel):
    destination_port: str = Field(..., example="Port Klang")
    tidal_window: str = Field(..., example="2026-08-19T23:00:00+08:00")
    transit_time_hours: int = Field(..., example=18)
    must_depart_by: str = Field(..., example="2026-08-19T05:00:00+08:00")
    buffer_hours: float = Field(1.0, example=1.0)


class DepartureWindow(BaseModel):
    earliest: str = Field(..., example="2026-08-19T14:00:00+08:00")
    latest: str = Field(..., example="2026-08-19T16:00:00+08:00")
    requested: str = Field(..., example="2026-08-19T14:00:00+08:00")


class SeaITTCapacityResponse(BaseModel):
    status: str = Field("success", example="success")
    feeder_id: str = Field(..., example="FEEDER ATLANTIC-03")
    feeder_operator: str = Field(..., example="PIL Shipping")
    vessel_type: str = Field("Feeder", example="Feeder")
    capacity_teu: int = Field(..., example=800)
    current_occupancy_teu: int = Field(..., example=620)
    available_capacity_teu: int = Field(..., example=180)
    berth_status: str = Field(..., example="berthed_at_PPT_B12")
    departure_window: DepartureWindow
    downstream_constraints: FeederDownstreamConstraints
    hold_cost_per_hour: int = Field(..., example=800)
    missed_connection_cost: int = Field(..., example=5000)


# ---------------------------------------------------------------------------
# Tool 4: compute_itt_split (internal computation)
# ---------------------------------------------------------------------------

class ITTSplitOption(BaseModel):
    road_containers: int = Field(..., example=80)
    road_breakdown: str = Field(..., example="40x 40ft (40 trips) + 40x 20ft (20 trips)")
    road_trips: int = Field(..., example=60)
    road_cost: int = Field(..., example=9000)
    sea_containers: int = Field(..., example=40)
    sea_marginal_charter_cost: int = Field(0, example=0)
    sea_terminal_handling_cost: int = Field(..., example=1400)
    total_transport_cost: int = Field(..., example=10400)
    cost_notes: str = Field("", example="Sea transfer has $0 marginal charter cost")
    risk: Optional[str] = Field(None, example="road_congestion_delay_near_pandan")


class ITTSplitTimeline(BaseModel):
    road_itt_arrival: str = Field(..., example="2026-08-19T14:30:00+08:00")
    sea_itt_arrival: str = Field(..., example="2026-08-19T16:30:00+08:00")
    tuas_loading_start: str = Field(..., example="2026-08-19T17:00:00+08:00")
    vessel_departure: str = Field(..., example="2026-08-19T20:00:00+08:00")
    margin_minutes: int = Field(180, example=180)


class ITTSplitResponse(BaseModel):
    status: str = Field("success", example="success")
    optimal_split: ITTSplitOption
    alternatives: list[ITTSplitOption]
    timeline: ITTSplitTimeline
    cost_vs_baseline: dict = Field(..., example={"baseline_all_road_cost": 12000, "optimised_transport_cost": 10400})


# ---------------------------------------------------------------------------
# Tool 5: update_tuas_loading_sequence (CITOS Tuas)
# ---------------------------------------------------------------------------

class QcAdjustment(BaseModel):
    qc_id: str = Field(..., example="QC-07")
    original_bay: str = Field(..., example="Bay14")
    new_bay: str = Field(..., example="Bay14")
    eta: str = Field(..., example="14:30")


class LoadingSequenceResponse(BaseModel):
    status: str = Field("success", example="success")
    vessel_id: str = Field(..., example="MV PACIFIC STAR")
    original_loading_sequence: str = Field(..., example="Bay14→Bay12→Bay10→Bay08")
    updated_loading_sequence: str = Field(..., example="Bay14(road@14:30)→Bay12(road@14:30)→Bay10(sea@16:30)→Bay08(sea@16:30)")
    qc_adjustments: list[QcAdjustment]
    estimated_loading_completion: str = Field(..., example="2026-08-19T19:30:00+08:00")
    margin_before_departure_minutes: int = Field(30, example=30)


# ---------------------------------------------------------------------------
# Tool 6: Webhook (ITT_COORDINATION_REQUEST event)
# ---------------------------------------------------------------------------

class ITTCoordinationEvent(BaseModel):
    event_type: str = Field(..., example="ITT_COORDINATION_REQUEST")
    timestamp: str = Field(..., example="2026-08-19T10:30:00+08:00")
    source: str = Field(..., example="CITOS_PPT")
    priority: str = Field(..., example="high")
    origin_terminal: str = Field("PPT")
    destination_terminal: str = Field("TUAS")
    vessel_id: str = Field(..., example="MV PACIFIC STAR")
    tuas_vessel_departure: str = Field(..., example="2026-08-19T20:00:00+08:00")
    container_count: int = Field(..., ge=50, example=120)
    containers_ready: int = Field(..., example=120)
    blocks_affected: list[str] = Field(..., example=["B-07", "B-08", "B-12", "B-14"])
    dg_containers: int = Field(0, ge=0, example=3)
    priority_containers: int = Field(0, ge=0, example=45)
    requested_by: str = Field(..., example="PPT_Yard_Planner_Lim")
    notes: str = Field("", example="Priority transhipment for MV PACIFIC STAR")


class WebhookResponse(BaseModel):
    status: str = Field("accepted")
    run_id: str
    message: str = "ITT coordination request received. Agent triggered."
