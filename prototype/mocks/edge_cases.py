"""Edge case simulation utilities — used ONLY by integration tests.

These functions simulate specific disruption scenarios per Master Charter §7:
- ec_1: Feeder berth conflict (departure delayed to 1600)
- ec_2: Data staleness (PPT CITOS data > 20 min old)

These are NOT exposed via any API endpoint. Import directly in test code only.
"""

from datetime import datetime, timedelta


def simulate_feeder_conflict(feeder_data: dict) -> dict:
    """
    Simulate feeder berth conflict (ec_1): departure delayed to 1600.
    Injects delay into feeder response data.
    """
    modified = feeder_data.copy()
    modified["berth_status"] = "berth_conflict_delayed"
    modified["departure_window"] = {
        "earliest": "2026-08-19T16:00:00+08:00",
        "latest": "2026-08-19T16:00:00+08:00",
        "requested": "2026-08-19T14:00:00+08:00",
    }
    modified["downstream_constraints"] = modified.get("downstream_constraints", {}).copy()
    modified["downstream_constraints"]["must_depart_by"] = "2026-08-19T15:30:00+08:00"
    modified["hold_cost_per_hour"] = 800
    modified["missed_connection_cost"] = 5000
    modified["edge_case"] = "feeder_berth_conflict"
    modified["edge_case_note"] = (
        "PORTNET reports feeder berth conflict — departure delayed to 1600. "
        "Feeder will miss downstream tidal window at Port Klang."
    )
    return modified


def simulate_stale_data(container_data: dict, stale_minutes: int = 25) -> dict:
    """
    Simulate data staleness (ec_2): PPT CITOS data is 25 min old.
    Adds stale timestamp to container response.
    """
    modified = container_data.copy()
    stale_time = (datetime.now() - timedelta(minutes=stale_minutes)).isoformat()
    modified["data_timestamp"] = stale_time
    modified["data_age_minutes"] = stale_minutes
    modified["edge_case"] = "data_staleness"
    modified["edge_case_note"] = (
        f"PPT CITOS data is {stale_minutes} min old — containers may not be ready. "
        "Trigger escalation."
    )
    return modified


# Edge case registry — maps case_id to inject function
EDGE_CASES = {
    "ec_1": {
        "name": "Feeder berth conflict",
        "inject_at_step": 8,
        "system": "feeder",
        "simulate": simulate_feeder_conflict,
    },
    "ec_2": {
        "name": "Data staleness",
        "inject_at_step": 2,
        "system": "citos_ppt",
        "simulate": simulate_stale_data,
    },
}
