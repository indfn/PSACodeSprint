"""Pydantic models for PPT CITOS mock API — matches Master Charter §3 Tool 1 schema."""

from pydantic import BaseModel, Field
from typing import Optional


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


class ITTCandidatesRequest(BaseModel):
    cit_ppt_endpoint: str = Field(..., example="CITOS_PPT")
    vessel_id: str = Field(..., example="MV PACIFIC STAR")


class YardStatusResponse(BaseModel):
    status: str = Field("success")
    terminal: str = Field("PPT")
    blocks: dict[str, dict]
    last_updated: str
    data_age_minutes: float


class WebhookEvent(BaseModel):
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
    dg_containers: int = Field(0, example=3)
    priority_containers: int = Field(0, example=45)
    requested_by: str = Field(..., example="PPT_Yard_Planner_Lim")
    notes: str = Field("", example="Priority transhipment for MV PACIFIC STAR")


class WebhookResponse(BaseModel):
    status: str = Field("accepted")
    run_id: str
    message: str = "ITT coordination request received. Agent triggered."
