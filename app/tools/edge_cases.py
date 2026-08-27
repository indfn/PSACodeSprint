from __future__ import annotations

import copy
from datetime import datetime, timedelta

from app.mocks import data as mock_data

"""
Demo-only edge injection hooks — not thread-safe.
Mutates module-global FEEDER_DATA / _stale_minutes so next tool call sees conflict/staleness.
reset_edge_cases() restores from deepcopy(_FEEDER_DATA_ORIGINAL) captured at import time;
concurrent injections need external locking or per-run copy. Tests use autouse fixture for isolation.
"""


def inject_feeder_berth_conflict(
    feeder_id: str = "FEEDER ATLANTIC-03",
    new_departure: str = "2026-08-19T16:00:00+08:00",
) -> dict:
    mock_data.FEEDER_DATA["feeder_id"] = feeder_id
    mock_data.FEEDER_DATA["berth_status"] = "conflict"
    dw = dict(mock_data.FEEDER_DATA.get("departure_window", {}))
    dw["latest"] = new_departure
    mock_data.FEEDER_DATA["departure_window"] = dw
    mock_data.FEEDER_DATA["conflict"] = True
    mock_data.FEEDER_DATA["delay_minutes"] = 120
    mock_data.FEEDER_DATA["edge_case"] = "feeder_berth_conflict"
    mock_data.FEEDER_DATA["edge_case_note"] = (
        "PORTNET reports feeder berth conflict — departure delayed to 1600. "
        "Feeder will miss downstream tidal window at Port Klang."
    )
    return copy.deepcopy(mock_data.FEEDER_DATA)


def inject_stale_data(time_offset_minutes: int = 25) -> dict:
    mock_data._stale_minutes = int(time_offset_minutes)
    return {
        "stale_minutes": mock_data._stale_minutes,
        "data_age_minutes": float(mock_data._stale_minutes),
        "edge_case": "data_staleness",
    }


def reset_edge_cases() -> dict:
    mock_data.FEEDER_DATA.clear()
    mock_data.FEEDER_DATA.update(copy.deepcopy(mock_data._FEEDER_DATA_ORIGINAL))
    mock_data._stale_minutes = 0
    return {"reset": True}
