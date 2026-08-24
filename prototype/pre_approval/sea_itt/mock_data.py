"""Realistic mock feeder vessel and downstream port data for Sea ITT.

Based on Master Charter §3 Tool 3 sample output and PSA Singapore
feeder vessel operations (PPT → Port Klang / Tanjung Pelepas corridor).

Feeder operations context:
  - PPT (Pasir Panjang Terminal) to Port Klang: ~18 hrs transit
  - PPT to Tanjung Pelepas: ~12 hrs transit
  - Feeder vessels typically 400-1200 TEU capacity
  - Tidal windows at Port Klang: ~6 hr intervals (spring/neap dependent)
  - Feeder charter rate: $800/hr (Master Charter §5)
"""

import copy
from datetime import datetime, timedelta, timezone
from typing import Any

SGT = timezone(timedelta(hours=8))


# ---------------------------------------------------------------------------
# Mock feeder fleet data
# ---------------------------------------------------------------------------

FEEDER_FLEET: dict[str, dict[str, Any]] = {
    "FEEDER ATLANTIC-03": {
        "feeder_id": "FEEDER ATLANTIC-03",
        "feeder_operator": "PIL Shipping",
        "vessel_type": "Feeder",
        "imo_number": "9876543",
        "capacity_teu": 800,
        "current_occupancy_teu": 620,
        "available_capacity_teu": 180,
        "berth_status": "berthed_at_PPT_B12",
        "departure_window": {
            "earliest": "2026-08-19T14:00:00+08:00",
            "latest": "2026-08-19T16:00:00+08:00",
            "requested": "2026-08-19T14:00:00+08:00",
        },
        "downstream_constraints": {
            "destination_port": "Port Klang",
            # Tidal window 23:00 — feeder must depart PPT by ~04:00 to catch it
            # (18 hrs transit + 1 hr buffer). But the feeder's scheduled rotation
            # from PPT departs 14:00-16:00, arriving Port Klang ~08:00 next day,
            # well AFTER the 23:00 window. This is realistic: the feeder will miss
            # this window and must wait for the NEXT tidal window (next day ~11:00).
            # The agent's job is to detect this and factor it into the ITT split.
            "tidal_window": "2026-08-20T11:00:00+08:00",
            "transit_time_hours": 18.0,
            "must_depart_by": "2026-08-20T04:00:00+08:00",
            "buffer_hours": 1.0,
        },
        "hold_cost_per_hour": 800.0,
        "missed_connection_cost": 5000.0,
    },
    "FEEDER INDO-07": {
        "feeder_id": "FEEDER INDO-07",
        "feeder_operator": "Evergreen Marine",
        "vessel_type": "Feeder",
        "imo_number": "9876544",
        "capacity_teu": 600,
        "current_occupancy_teu": 510,
        "available_capacity_teu": 90,
        "berth_status": "berthed_at_PPT_B08",
        "departure_window": {
            "earliest": "2026-08-19T15:00:00+08:00",
            "latest": "2026-08-19T17:00:00+08:00",
            "requested": "2026-08-19T15:30:00+08:00",
        },
        "downstream_constraints": {
            "destination_port": "Tanjung Pelepas",
            "tidal_window": "2026-08-19T21:00:00+08:00",
            "transit_time_hours": 12.0,
            "must_depart_by": "2026-08-19T09:00:00+08:00",
            "buffer_hours": 1.0,
        },
        "hold_cost_per_hour": 650.0,
        "missed_connection_cost": 3500.0,
    },
    "FEEDER MAL-12": {
        "feeder_id": "FEEDER MAL-12",
        "feeder_operator": "MISC Berhad",
        "vessel_type": "Feeder",
        "imo_number": "9876545",
        "capacity_teu": 1000,
        "current_occupancy_teu": 880,
        "available_capacity_teu": 120,
        "berth_status": "anchored_waiting",
        "departure_window": {
            "earliest": "2026-08-19T18:00:00+08:00",
            "latest": "2026-08-19T20:00:00+08:00",
            "requested": "2026-08-19T18:00:00+08:00",
        },
        "downstream_constraints": {
            "destination_port": "Port Klang",
            "tidal_window": "2026-08-20T05:00:00+08:00",
            "transit_time_hours": 18.0,
            "must_depart_by": "2026-08-19T11:00:00+08:00",
            "buffer_hours": 1.0,
        },
        "hold_cost_per_hour": 900.0,
        "missed_connection_cost": 6000.0,
    },
    "FEEDER SL-05": {
        "feeder_id": "FEEDER SL-05",
        "feeder_operator": "CMA CGM",
        "vessel_type": "Feeder",
        "imo_number": "9876546",
        "capacity_teu": 500,
        "current_occupancy_teu": 380,
        "available_capacity_teu": 120,
        "berth_status": "departed_ppt",
        "departure_window": {
            "earliest": "2026-08-19T08:00:00+08:00",
            "latest": "2026-08-19T08:00:00+08:00",
            "requested": "2026-08-19T08:00:00+08:00",
        },
        "downstream_constraints": {
            "destination_port": "Colombo",
            "tidal_window": "2026-08-20T12:00:00+08:00",
            "transit_time_hours": 72.0,
            "must_depart_by": "2026-08-19T08:00:00+08:00",
            "buffer_hours": 2.0,
        },
        "hold_cost_per_hour": 700.0,
        "missed_connection_cost": 4000.0,
    },
}


# ---------------------------------------------------------------------------
# Berth conflict scenario (for edge case injection)
# ---------------------------------------------------------------------------

FEEDER_BERTH_CONFLICT: dict[str, Any] = {
    "feeder_id": "FEEDER ATLANTIC-03",
    "departure_status": "delayed",
    "delay_minutes": 120,  # 2-hour delay
    "berth_conflict": True,
    "conflict_vessel": "MV OCEAN GLORY",
    "conflict_reason": "Emergency berth reallocation — MV OCEAN GLORY priority arrival",
    "new_departure_window": {
        "earliest": "2026-08-19T16:00:00+08:00",
        "latest": "2026-08-19T18:00:00+08:00",
    },
    "message": (
        "Feeder berth conflict detected: MV OCEAN GLORY has been allocated to "
        "B12 due to emergency priority. FEEDER ATLANTIC-03 departure delayed "
        "from 1400 to 1600."
    ),
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

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
        # Skip departed vessels
        if feeder["berth_status"] == "departed_ppt":
            continue

        # Skip if no capacity
        if feeder["available_capacity_teu"] <= 0:
            continue

        # Check departure window hasn't passed
        dep_latest = datetime.fromisoformat(feeder["departure_window"]["latest"])
        if dep_latest <= now:
            continue

        available.append(feeder)

    return available


def get_feeder_for_itc_selection() -> dict[str, Any]:
    """Get the primary feeder for ITT coordination — FEEDER ATLANTIC-03.

    This is the default feeder used in the PB-12 demo scenario.
    Matches Master Charter §3 Tool 3 sample output.
    """
    return FEEDER_FLEET["FEEDER ATLANTIC-03"].copy()


def simulate_berth_conflict(feeder_id: str = "FEEDER ATLANTIC-03") -> dict[str, Any]:
    """Simulate a berth conflict for edge case testing.

    Injected at Step 8 of the demo (see Master Charter §7 Scenario A).
    Triggers esc_6 (feeder unresponsive > 15 min) and esc_2 (feeder hold > 1.5 hrs).

    Returns updated feeder data with delayed departure window. The tool function
    reads 'new_departure_window' to update the departure constraints.
    """
    base = get_feeder_status(feeder_id)
    if not base:
        return {"status": "error", "error": f"Feeder {feeder_id} not found"}

    # Deep copy to avoid mutating shared FEEDER_FLEET state (CR-01 fix)
    conflict = copy.deepcopy(base)

    # Delay departure by 2 hours from the original earliest
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
    For the mock, returns realistic tidal window data.
    """
    ports = {
        "Port Klang": {
            "port_name": "Port Klang",
            "country": "Malaysia",
            "transit_time_hours": 18.0,
            "tidal_type": "mixed_semidiurnal",
            "next_tidal_window": "2026-08-19T23:00:00+08:00",
            "tidal_window_duration_hours": 6.0,
            "draft_limit_meters": 14.5,
            "pilot_available_24h": True,
        },
        "Tanjung Pelepas": {
            "port_name": "Tanjung Pelepas",
            "country": "Malaysia",
            "transit_time_hours": 12.0,
            "tidal_type": "diurnal",
            "next_tidal_window": "2026-08-19T21:00:00+08:00",
            "tidal_window_duration_hours": 5.0,
            "draft_limit_meters": 16.0,
            "pilot_available_24h": True,
        },
        "Colombo": {
            "port_name": "Colombo",
            "country": "Sri Lanka",
            "transit_time_hours": 72.0,
            "tidal_type": "semidiurnal",
            "next_tidal_window": "2026-08-20T12:00:00+08:00",
            "tidal_window_duration_hours": 8.0,
            "draft_limit_meters": 15.0,
            "pilot_available_24h": True,
        },
    }

    return ports.get(destination_port, {
        "port_name": destination_port,
        "country": "Unknown",
        "transit_time_hours": 24.0,
        "tidal_type": "unknown",
        "next_tidal_window": None,
        "tidal_window_duration_hours": 0,
        "draft_limit_meters": 12.0,
        "pilot_available_24h": False,
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

    # Determine tidal risk based on hold duration
    downstream = feeder["downstream_constraints"]
    tidal_window = datetime.fromisoformat(downstream["tidal_window"])
    transit_hours = downstream["transit_time_hours"]
    buffer_hours = downstream["buffer_hours"]

    # Latest safe departure = tidal_window - transit - buffer
    dep_window_latest = datetime.fromisoformat(feeder["departure_window"]["latest"])
    latest_safe_departure = tidal_window - timedelta(hours=transit_hours + buffer_hours)

    # New projected departure after hold
    new_departure = dep_window_latest + timedelta(hours=hold_hours)

    # Risk assessment
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
