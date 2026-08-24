"""Pydantic models for Sea ITT Mock API — matches Master Charter §3 Tool 3 schema.

Covers:
  - Feeder vessel availability and berth status
  - Departure window constraints
  - Downstream port tidal window and connection deadlines
  - Integration with Tool 4 (compute_itt_split) sea_capacity parameter
"""

from pydantic import BaseModel, Field
from typing import Optional


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class SeaITTCapacityRequest(BaseModel):
    """Request to check sea ITT capacity for a specific feeder."""
    portnet_endpoint: str = Field(
        ..., example="PORTNET",
        description="PORTNET system endpoint identifier",
    )
    feeder_id: str = Field(
        ..., example="FEEDER ATLANTIC-03",
        description="Feeder vessel identifier",
    )
    current_time: str = Field(
        ..., example="2026-08-19T10:35:00+08:00",
        description="ISO-8601 current timestamp for capacity check",
    )


class FeederHoldRequest(BaseModel):
    """Request to hold a feeder vessel at berth."""
    portnet_endpoint: str = Field(..., example="PORTNET")
    feeder_id: str = Field(..., example="FEEDER ATLANTIC-03")
    hold_hours: float = Field(
        ..., gt=0, le=6, example=1.0,
        description="Number of hours to request hold (max 6)",
    )


# ---------------------------------------------------------------------------
# Response sub-models
# ---------------------------------------------------------------------------

class DepartureWindow(BaseModel):
    """Feeder departure time window at PPT."""
    earliest: str = Field(
        ..., example="2026-08-19T14:00:00+08:00",
        description="Earliest possible departure (ISO-8601)",
    )
    latest: str = Field(
        ..., example="2026-08-19T16:00:00+08:00",
        description="Latest possible departure (ISO-8601)",
    )
    requested: str = Field(
        ..., example="2026-08-19T14:00:00+08:00",
        description="Operator-requested departure time (ISO-8601)",
    )


class DownstreamConstraints(BaseModel):
    """Downstream port constraints — tidal windows, transit time, deadlines."""
    destination_port: str = Field(
        ..., example="Port Klang",
        description="Feeder's next port of call after PPT",
    )
    tidal_window: str = Field(
        ..., example="2026-08-19T23:00:00+08:00",
        description="Next tidal window at destination (ISO-8601) — vessel must arrive before this",
    )
    transit_time_hours: float = Field(
        ..., example=18.0,
        description="Transit time from PPT to downstream port in hours",
    )
    must_depart_by: str = Field(
        ..., example="2026-08-19T04:00:00+08:00",
        description=(
            "Latest departure from PPT to catch tidal window (ISO-8601). "
            "Informational only — the tool computes its own deadline from "
            "tidal_window - transit_time - buffer. Use this field for "
            "port-authority-specific overrides if needed."
        ),
    )
    buffer_hours: float = Field(
        ..., example=1.0,
        description="Safety buffer before tidal window deadline (hours)",
    )


class FeederCapacity(BaseModel):
    """Feeder vessel capacity details."""
    capacity_teu: int = Field(
        ..., example=800,
        description="Total feeder capacity in TEU",
    )
    current_occupancy_teu: int = Field(
        ..., example=620,
        description="Currently loaded TEU",
    )
    available_capacity_teu: int = Field(
        ..., example=180,
        description="Available capacity for ITT containers (TEU)",
    )


# ---------------------------------------------------------------------------
# Main response model
# ---------------------------------------------------------------------------

class SeaITTCapacityResponse(BaseModel):
    """Complete sea ITT capacity response — matches Master Charter §3 Tool 3."""
    status: str = Field("success", example="success")
    feeder_id: str = Field(..., example="FEEDER ATLANTIC-03")
    feeder_operator: str = Field(..., example="PIL Shipping")
    vessel_type: str = Field("Feeder", example="Feeder")
    capacity: FeederCapacity
    berth_status: str = Field(
        ..., example="berthed_at_PPT_B12",
        description="Current berth status at PPT",
    )
    departure_window: DepartureWindow
    downstream_constraints: DownstreamConstraints
    hold_cost_per_hour: float = Field(
        ..., example=800.0,
        description="Cost per hour for holding feeder at berth (SGD)",
    )
    missed_connection_cost: float = Field(
        ..., example=5000.0,
        description="Cost if feeder misses downstream connection (SGD)",
    )
    data_timestamp: Optional[str] = Field(
        None, example="2026-08-19T10:35:00+08:00",
        description="Timestamp of data retrieval (for staleness checks)",
    )
    data_age_minutes: Optional[float] = Field(
        None, example=0.5,
        description="Age of data in minutes (for esc_4 trigger)",
    )


class FeederHoldResponse(BaseModel):
    """Response to a feeder hold request."""
    status: str = Field("success")
    feeder_id: str
    hold_hours: float
    hold_cost: float = Field(
        ..., description="Total cost of hold (hold_hours × hold_cost_per_hour)",
    )
    new_departure: str = Field(
        ..., description="Projected new departure time after hold (ISO-8601)",
    )
    tidal_risk: str = Field(
        ..., description="Risk assessment: 'safe', 'marginal', or 'critical'",
    )
    message: str = ""


class FeederStatusResponse(BaseModel):
    """Lightweight feeder status check (for monitoring / edge case detection)."""
    status: str = Field("success")
    feeder_id: str
    berth_status: str
    departure_status: str = Field(
        ..., example="on_schedule",
        description="on_schedule | delayed | berth_conflict | departed",
    )
    delay_minutes: int = Field(
        0, example=0,
        description="Delay in minutes from originally scheduled departure",
    )
    berth_conflict: bool = Field(
        False, description="True if another vessel has claimed the berth",
    )
    data_timestamp: str
