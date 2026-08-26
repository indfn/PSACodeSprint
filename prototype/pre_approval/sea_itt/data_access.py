"""Data access layer for Sea ITT.

Provides query functions over feeder fleet and downstream port mock data.
All static data loaded from mock_data.yaml.
"""

from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from prototype.shared.utils.yaml_reader import load_yaml

_MODULE_DIR = Path(__file__).resolve().parent
_MOCK_DATA = load_yaml(_MODULE_DIR / "mock_data.yaml")

SGT = timezone(timedelta(hours=8))

FEEDER_FLEET: dict[str, dict[str, Any]] = _MOCK_DATA["feeder_fleet"]
FEEDER_BERTH_CONFLICT: dict[str, Any] = _MOCK_DATA["feeder_berth_conflict"]
_DOWNSTREAM_PORTS: dict[str, dict[str, Any]] = _MOCK_DATA["downstream_ports"]
_DEFAULT_DOWNSTREAM: dict[str, Any] = _MOCK_DATA["default_downstream_port"]


def get_feeder_status(feeder_id: str) -> dict[str, Any] | None:
    """Get current feeder status by ID."""
    return FEEDER_FLEET.get(feeder_id)


def get_available_feeders(current_time: datetime | None = None) -> list[dict[str, Any]]:
    """Get all feeders that are available for ITT loading.

    Filters:
      - Must be berthed at PPT (not departed)
      - Must have available capacity > 0
      - Departure window must not have passed
    """
    available = []
    now = current_time or datetime.now(SGT)

    for feeder in FEEDER_FLEET.values():
        if feeder["berth_status"] == "departed_ppt":
            continue
        if feeder["available_capacity_teu"] <= 0:
            continue
        dep_latest = datetime.fromisoformat(feeder["departure_window"]["latest"])
        if dep_latest <= now:
            continue
        available.append(feeder)

    return available


def get_feeder_for_itc_selection() -> dict[str, Any]:
    """Get the primary feeder for ITT coordination — FEEDER ATLANTIC-03."""
    return FEEDER_FLEET["FEEDER ATLANTIC-03"].copy()


def simulate_berth_conflict(feeder_id: str = "FEEDER ATLANTIC-03") -> dict[str, Any]:
    """Simulate a berth conflict for edge case testing.

    Injected at Step 8 of the demo (see Master Charter §7 Scenario A).
    Returns updated feeder data with delayed departure window.
    """
    base = get_feeder_status(feeder_id)
    if not base:
        return {"status": "error", "error": f"Feeder {feeder_id} not found"}

    conflict = copy.deepcopy(base)

    original_earliest = datetime.fromisoformat(conflict["departure_window"]["earliest"])
    delayed_earliest = original_earliest + timedelta(hours=2)
    delayed_latest = delayed_earliest + timedelta(hours=2)

    conflict["departure_status"] = "delayed"
    conflict["delay_minutes"] = 120
    conflict["berth_conflict"] = True
    conflict["conflict_vessel"] = "MV OCEAN GLORY"
    conflict["conflict_reason"] = "Emergency berth reallocation — MV OCEAN GLORY priority arrival"
    conflict["new_departure_window"] = {
        "earliest": delayed_earliest.isoformat(),
        "latest": delayed_latest.isoformat(),
    }
    conflict["message"] = (
        f"Feeder berth conflict detected: MV OCEAN GLORY has been allocated to "
        f"B12 due to emergency priority. {feeder_id} departure delayed "
        f"from {original_earliest.strftime('%H:%M')} to {delayed_earliest.strftime('%H:%M')}."
    )
    conflict["data_timestamp"] = datetime.now(SGT).isoformat()
    return conflict


def get_downstream_port_info(destination_port: str = "Port Klang") -> dict[str, Any]:
    """Get downstream port tidal window and transit information.

    In production this would query MPA VTIS or port authority APIs.
    """
    return _DOWNSTREAM_PORTS.get(destination_port, {
        **_DEFAULT_DOWNSTREAM,
        "port_name": destination_port,
    })


def get_feeder_hold_cost(
    feeder_id: str,
    hold_hours: float,
) -> dict[str, Any]:
    """Compute cost and risk of holding a feeder at berth."""
    if hold_hours <= 0 or hold_hours > 6:
        return {"status": "error", "error": f"hold_hours must be between 0 and 6, got {hold_hours}"}

    feeder = get_feeder_status(feeder_id)
    if not feeder:
        return {"status": "error", "error": f"Feeder {feeder_id} not found"}

    hold_cost_per_hour = feeder["hold_cost_per_hour"]
    total_hold_cost = hold_cost_per_hour * hold_hours

    downstream = feeder["downstream_constraints"]
    tidal_window = datetime.fromisoformat(downstream["tidal_window"])
    transit_hours = downstream["transit_time_hours"]
    buffer_hours = downstream["buffer_hours"]

    dep_window_latest = datetime.fromisoformat(feeder["departure_window"]["latest"])
    latest_safe_departure = tidal_window - timedelta(hours=transit_hours + buffer_hours)

    new_departure = dep_window_latest + timedelta(hours=hold_hours)

    if new_departure <= latest_safe_departure:
        tidal_risk = "safe"
    elif new_departure <= latest_safe_departure + timedelta(hours=1):
        tidal_risk = "marginal"
    else:
        tidal_risk = "critical"

    return {
        "status": "success",
        "feeder_id": feeder_id,
        "hold_hours": hold_hours,
        "hold_cost_per_hour": hold_cost_per_hour,
        "total_hold_cost": total_hold_cost,
        "new_departure": new_departure.isoformat(),
        "latest_safe_departure": latest_safe_departure.isoformat(),
        "tidal_risk": tidal_risk,
        "missed_connection_cost": feeder["missed_connection_cost"],
        "message": (
            f"Holding {feeder_id} for {hold_hours}hr costs ${total_hold_cost:,.0f}. "
            f"Tidal risk: {tidal_risk}."
        ),
    }
