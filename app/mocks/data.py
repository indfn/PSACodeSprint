"""Realistic mock data for PSA systems — grounded in Master Charter cost parameters."""

from datetime import datetime, timedelta
import copy
import random

notification_log: list[dict] = []


# ---------------------------------------------------------------------------
# Cost parameters (Master Charter §5)
# ---------------------------------------------------------------------------

COST_PARAMS = {
    "road_cost_per_trip": 150,
    "vessel_demurrage_per_hr": 2500,
    "feeder_charter_per_hr": 800,
    "sea_terminal_handling": 35,       # per lift-move
    "yard_rehandle": 35,
    "staff_hourly": 50,
    "missed_connection_per_container": 150,
}


# ---------------------------------------------------------------------------
# Container data (CITOS PPT) — 120 containers across 4 yard blocks
# ---------------------------------------------------------------------------

CONSIGNEES = [
    "DB Schenker", "Kuehne+Nagel", "DHL Supply Chain", "Sinotrans",
    "CMA CGM Logistics", "Maersk Logistics", "PSA Marine", "YCH Group",
    "CEVA Logistics", "Agility Logistics", "Bolloré Logistics", "Expeditors",
]

DESTINATION_PORTS = [
    "LA", "Rotterdam", "Port Klang", "Tanjung Pelepas", "Laem Chabang",
    "Hai Phong", "Shanghai", "Busan", "Colombo", "Dubai",
]

YARD_BLOCKS = ["B-07", "B-08", "B-12", "B-14"]


def _generate_container_id(index: int) -> str:
    prefixes = ["MSKU", "TCLU", "CMAU", "SEGU", "PCIU", "EISU", "KKFU", "OOLU"]
    prefix = prefixes[index % len(prefixes)]
    number = 1000000 + (index * 7919) % 9000000
    return f"{prefix}{number}"


def _generate_yard_position(block_num: int, index: int) -> tuple[str, str]:
    bay = (index % 20) + 1
    row = (index % 6) + 1
    tier = (index % 4) + 1
    return f"B-{block_num:02d}", f"Bay {bay:02d} Row {row:02d} Tier {tier:02d}"


def generate_containers() -> list[dict]:
    """Generate 120 containers: 40x 40ft + 80x 20ft = 160 TEU, 3 DG."""
    rng = random.Random(42)

    containers = []
    dg_count = 0

    for i in range(120):
        size = "40ft" if i < 40 else "20ft"
        block_idx = i % 4
        yard_block, yard_position = _generate_yard_position(
            int(YARD_BLOCKS[block_idx].split("-")[1]), i
        )

        weight = rng.randint(18000, 32000) if size == "40ft" else rng.randint(8000, 18000)

        dg_class = None
        if dg_count < 3 and rng.random() < 0.05:
            dg_class = rng.choice(["3", "8"])
            dg_count += 1

        priority = "high" if i < 45 else "standard"

        containers.append({
            "container_id": _generate_container_id(i),
            "size": size,
            "yard_block": yard_block,
            "yard_position": yard_position,
            "weight_kg": weight,
            "dg_class": dg_class,
            "priority": priority,
            "consignee": rng.choice(CONSIGNEES),
            "destination_port": rng.choice(DESTINATION_PORTS),
            "ready_for_itt": True,
        })

    while dg_count < 3:
        idx = rng.randint(0, len(containers) - 1)
        if containers[idx]["dg_class"] is None:
            containers[idx]["dg_class"] = rng.choice(["3", "8"])
            dg_count += 1

    return containers


_stale_minutes: int = 0


def get_container_data(vessel_id: str = "MV PACIFIC STAR") -> dict:
    """CITOS PPT container readiness — Tool 1 response."""
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

    result: dict = {
        "status": "success",
        "vessel_id": vessel_id,
        "tuas_departure": "2026-08-19T20:00:00+08:00",
        "total_containers": len(containers),
        "total_teu": len(fortyft) * 2 + len(twentyft),
        "container_breakdown": {"40ft_feu": len(fortyft), "20ft_teu": len(twentyft)},
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

    if _stale_minutes > 0:
        result["data_timestamp"] = (datetime.now() - timedelta(minutes=_stale_minutes)).isoformat()
        result["data_age_minutes"] = float(_stale_minutes)
        result["edge_case"] = "data_staleness"
        result["edge_case_note"] = f"PPT CITOS data is {_stale_minutes} min old — containers may not be ready."
    else:
        result["data_timestamp"] = datetime.now().isoformat()
        result["data_age_minutes"] = 0.5

    return result


# ---------------------------------------------------------------------------
# Truck data (OptETruck) — road ITT capacity
# ---------------------------------------------------------------------------

TRUCK_DATA = {
    "available_trucks": 50,
    "total_fleet": 55,
    "transit_time_minutes": 90,
    "road_conditions": {
        "AYE": "normal",
        "West_Coast_Highway": "moderate_traffic_near_pandan",
        "Tuas_Port_Boulevard": "clear",
    },
    "cost_per_trip": COST_PARAMS["road_cost_per_trip"],
    "lta_chassis_limits": "1x 40ft/45ft (FEU) OR up to 2x 20ft (TEU) per prime mover",
    "estimated_round_trip_minutes": 210,
    "baseline_trips_all_120_containers": 80,
    "baseline_road_cost_all_120": 80 * COST_PARAMS["road_cost_per_trip"],
}


def get_truck_data(terminal: str = "PPT") -> dict:
    """OptETruck road ITT capacity — Tool 2 response."""
    return {
        "status": "success",
        "terminal": terminal,
        **TRUCK_DATA,
        "earliest_departure": "2026-08-19T11:00:00+08:00",
        "latest_arrival_at_tuas": "2026-08-19T18:00:00+08:00",
        "capacity_ratio": round(20 / 80, 2),
    }


# ---------------------------------------------------------------------------
# Feeder data (PORTNET) — sea ITT capacity
# ---------------------------------------------------------------------------

FEEDER_DATA = {
    "feeder_id": "FEEDER ATLANTIC-03",
    "feeder_operator": "PIL Shipping",
    "vessel_type": "Feeder",
    "capacity_teu": 800,
    "current_occupancy_teu": 620,
    "berth_status": "berthed_at_PPT_B12",
    "departure_window": {
        "earliest": "2026-08-19T14:00:00+08:00",
        "latest": "2026-08-19T16:00:00+08:00",
        "requested": "2026-08-19T14:00:00+08:00",
    },
    "downstream_constraints": {
        "destination_port": "Port Klang",
        "tidal_window": "2026-08-19T23:00:00+08:00",
        "transit_time_hours": 18,
        "must_depart_by": "2026-08-19T05:00:00+08:00",
        "buffer_hours": 1.0,
    },
    "hold_cost_per_hour": COST_PARAMS["feeder_charter_per_hr"],
    "missed_connection_cost": 5000,
}

_FEEDER_DATA_ORIGINAL: dict = copy.deepcopy(FEEDER_DATA)


def get_feeder_data(feeder_id: str = "FEEDER ATLANTIC-03") -> dict:
    """PORTNET sea ITT capacity — Tool 3 response."""
    return {
        "status": "success",
        **FEEDER_DATA,
        "feeder_id": feeder_id,
        "available_capacity_teu": FEEDER_DATA["capacity_teu"] - FEEDER_DATA["current_occupancy_teu"],
    }


# ---------------------------------------------------------------------------
# Tuas yard data (CITOS Tuas) — loading sequence
# ---------------------------------------------------------------------------

TUAS_YARD_DATA = {
    "vessel_id": "MV PACIFIC STAR",
    "original_loading_sequence": "Bay14→Bay12→Bay10→Bay08",
    "qc_assignments": [
        {"qc_id": "QC-07", "bay": "Bay14", "status": "available"},
        {"qc_id": "QC-07", "bay": "Bay12", "status": "available"},
        {"qc_id": "QC-08", "bay": "Bay10", "status": "available"},
        {"qc_id": "QC-08", "bay": "Bay08", "status": "available"},
    ],
    "block_capacity": 4500,
}


def get_loading_sequence_data(
    vessel_id: str = "MV PACIFIC STAR",
    itt_eta_road: str = "14:30",
    itt_eta_sea: str = "16:30",
) -> dict:
    """CITOS Tuas loading sequence — Tool 5 response."""
    return {
        "status": "success",
        "vessel_id": vessel_id,
        "original_loading_sequence": TUAS_YARD_DATA["original_loading_sequence"],
        "updated_loading_sequence": (
            f"Bay14(road@{itt_eta_road})→Bay12(road@{itt_eta_road})"
            f"→Bay10(sea@{itt_eta_sea})→Bay08(sea@{itt_eta_sea})"
        ),
        "qc_adjustments": [
            {"qc_id": "QC-07", "original_bay": "Bay14", "new_bay": "Bay14", "eta": itt_eta_road},
            {"qc_id": "QC-07", "original_bay": "Bay12", "new_bay": "Bay12", "eta": itt_eta_road},
            {"qc_id": "QC-08", "original_bay": "Bay10", "new_bay": "Bay10", "eta": itt_eta_sea},
            {"qc_id": "QC-08", "original_bay": "Bay08", "new_bay": "Bay08", "eta": itt_eta_sea},
        ],
        "estimated_loading_completion": "2026-08-19T19:30:00+08:00",
        "margin_before_departure_minutes": 30,
    }


# ---------------------------------------------------------------------------
# Split computation (Tool 4) — internal, not a mock API
# ---------------------------------------------------------------------------

def compute_itt_split_default() -> dict:
    """Default optimal split: 80 road / 40 sea = $10,400 total."""
    return {
        "status": "success",
        "optimal_split": {
            "road_containers": 80,
            "road_breakdown": "40x 40ft (40 trips) + 40x 20ft (20 trips)",
            "road_trips": 60,
            "road_cost": 9000,
            "sea_containers": 40,
            "sea_marginal_charter_cost": 0,
            "sea_terminal_handling_cost": 40 * COST_PARAMS["sea_terminal_handling"],
            "total_transport_cost": 9000 + 40 * COST_PARAMS["sea_terminal_handling"],
            "cost_notes": (
                "Sea transfer has $0 marginal charter cost (scheduled feeder rotation) "
                f"+ $1,400 terminal handling ($35/lift across 40 containers)"
            ),
        },
        "alternatives": [
            {
                "road_containers": 100,
                "road_breakdown": "40x 40ft (40 trips) + 60x 20ft (30 trips)",
                "road_trips": 70,
                "road_cost": 10500,
                "sea_containers": 20,
                "sea_marginal_charter_cost": 0,
                "sea_terminal_handling_cost": 20 * COST_PARAMS["sea_terminal_handling"],
                "total_transport_cost": 10500 + 20 * COST_PARAMS["sea_terminal_handling"],
                "risk": "road_congestion_delay_near_pandan",
            },
            {
                "road_containers": 60,
                "road_breakdown": "40x 40ft (40 trips) + 20x 20ft (10 trips)",
                "road_trips": 50,
                "road_cost": 7500,
                "sea_containers": 60,
                "sea_marginal_charter_cost": 0,
                "sea_terminal_handling_cost": 60 * COST_PARAMS["sea_terminal_handling"],
                "total_transport_cost": 7500 + 60 * COST_PARAMS["sea_terminal_handling"],
                "risk": "feeder_capacity_exceeded_20TEU",
            },
        ],
        "timeline": {
            "road_itt_arrival": "2026-08-19T14:30:00+08:00",
            "sea_itt_arrival": "2026-08-19T16:30:00+08:00",
            "tuas_loading_start": "2026-08-19T17:00:00+08:00",
            "vessel_departure": "2026-08-19T20:00:00+08:00",
            "margin_minutes": 180,
        },
        "cost_vs_baseline": {
            "baseline_all_road_cost": 80 * COST_PARAMS["road_cost_per_trip"],
            "baseline_all_road_trips": 80,
            "optimised_transport_cost": 9000 + 40 * COST_PARAMS["sea_terminal_handling"],
            "direct_transport_savings": (
                80 * COST_PARAMS["road_cost_per_trip"]
                - (9000 + 40 * COST_PARAMS["sea_terminal_handling"])
            ),
        },
    }
