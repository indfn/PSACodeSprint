"""Data access layer for PPT CITOS.

Provides query functions over mock container data.
All static data loaded from mock_data.yaml and ppt_citos_params.yaml.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from prototype.configs import load_config
from prototype.shared.utils.yaml_reader import load_yaml

from .mock_fakers import generate_containers

_MODULE_DIR = Path(__file__).resolve().parent
_PARAMS = load_config("ppt_citos_params.yaml")
_MOCK_DATA = load_yaml(_MODULE_DIR / "mock_data.yaml")

_DEFAULT_VESSEL_ID = _PARAMS["default_vessel_id"]
_TUAS_DEPARTURE = _PARAMS["tuas_departure"]
_YARD_BLOCK_STATUS = _MOCK_DATA["yard_block_status"]


def get_itt_candidates(vessel_id: str | None = None) -> dict[str, Any]:
    """Full ITT candidates response — matches Master Charter §3 Tool 1 schema."""
    vessel_id = vessel_id or _DEFAULT_VESSEL_ID
    containers = generate_containers()

    fortyft = [c for c in containers if c["size"] == "40ft"]
    twentyft = [c for c in containers if c["size"] == "20ft"]
    dg = [c for c in containers if c["dg_class"] is not None]

    seen_blocks: set[str] = set()
    blocks_affected: list[str] = []
    for c in containers:
        if c["yard_block"] not in seen_blocks:
            seen_blocks.add(c["yard_block"])
            blocks_affected.append(c["yard_block"])

    return {
        "status": "success",
        "vessel_id": vessel_id,
        "tuas_departure": _TUAS_DEPARTURE,
        "total_containers": len(containers),
        "total_teu": len(fortyft) * 2 + len(twentyft),
        "container_breakdown": {
            "40ft_feu": len(fortyft),
            "20ft_teu": len(twentyft),
        },
        "lta_truck_trip_requirement": {
            "40ft_feu_trips": len(fortyft),
            "20ft_teu_trips": len(twentyft) // 2,
            "total_potential_truck_trips_100pct_road": len(fortyft) + len(twentyft) // 2,
        },
        "containers": containers,
        "blocks_affected": blocks_affected,
        "dg_containers": len(dg),
        "reefer_containers": 0,
    }


def get_itt_candidates_stale(
    vessel_id: str | None = None,
    age_minutes: float = 25.0,
) -> dict[str, Any]:
    """Returns ITT candidates with a simulated data age for staleness edge case."""
    vessel_id = vessel_id or _DEFAULT_VESSEL_ID
    result = get_itt_candidates(vessel_id)
    result["data_timestamp"] = (
        datetime.now() - timedelta(minutes=age_minutes)
    ).isoformat()
    result["data_age_minutes"] = age_minutes
    return result


def get_yard_status() -> dict[str, Any]:
    """Return yard block occupancy status for all affected blocks."""
    return {
        "status": "success",
        "terminal": "PPT",
        "blocks": _YARD_BLOCK_STATUS,
        "last_updated": datetime.now().isoformat(),
        "data_age_minutes": 0.5,
    }
