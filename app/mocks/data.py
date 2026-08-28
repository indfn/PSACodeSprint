"""Realistic mock data for PSA systems — grounded in Master Charter cost parameters.

Supports scenario-based randomization via app.mocks.scenarios.
When a scenario is active, data generators randomize within scenario distributions.
When no scenario is active, returns deterministic hardcoded data (backward compatible).
"""

from datetime import datetime, timedelta, timezone
import copy
import random

notification_log: list[dict] = []


def _get_scenario_rng() -> random.Random | None:
    """Get the active scenario RNG, or None if no scenario is set."""
    try:
        from app.mocks.scenarios import _active_scenario_id, _rng
        if _active_scenario_id:
            return _rng
    except ImportError:
        pass
    return None


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


def generate_containers(count: int = 120, dg_target: int = 3, priority_ratio: float = 0.375, rng: random.Random | None = None) -> list[dict]:
    """Generate containers: 40ft + 20ft mix, DG, priority.

    When called from scenario system, count/dg_target/priority_ratio/rng are
    provided. When called standalone, defaults match old hardcoded behavior.
    """
    if rng is None:
        rng = random.Random(42)  # deterministic backward-compatible default

    containers = []
    dg_count = 0
    high_priority_count = int(count * priority_ratio)

    for i in range(count):
        size = "40ft" if rng.random() < 0.33 else "20ft"
        block_idx = i % 4
        yard_block, yard_position = _generate_yard_position(
            int(YARD_BLOCKS[block_idx].split("-")[1]), i
        )

        weight = rng.randint(18000, 32000) if size == "40ft" else rng.randint(8000, 18000)

        dg_class = None
        if dg_count < dg_target and rng.random() < 0.05:
            dg_class = rng.choice(["3", "8"])
            dg_count += 1

        priority = "high" if i < high_priority_count else "standard"

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

    while dg_count < dg_target:
        idx = rng.randint(0, len(containers) - 1)
        if containers[idx]["dg_class"] is None:
            containers[idx]["dg_class"] = rng.choice(["3", "8"])
            dg_count += 1

    return containers


_stale_minutes: int = 0
# Per-run overrides for concurrency isolation (Plan §6.12)
_overrides: dict[str, dict] = {}
_stale_overrides: dict[str, int] = {}


def get_container_data(vessel_id: str = "MV PACIFIC STAR", run_id: str = "") -> dict:
    """CITOS PPT container readiness — Tool 1 response.

    When a scenario is active, generates randomized data within scenario distributions.
    Otherwise returns deterministic hardcoded data (backward compatible).
    """
    # Check if scenario is active
    from app.mocks.scenarios import _active_scenario_id, _rng, PB12_SCENARIOS
    if _active_scenario_id and _active_scenario_id in PB12_SCENARIOS:
        sc = PB12_SCENARIOS[_active_scenario_id]
        containers = generate_containers(
            count=sc.container_count.sample_int(_rng),
            dg_target=sc.dg_count.sample_int(_rng),
            priority_ratio=sc.priority_ratio.sample(_rng),
            rng=_rng,
        )
    else:
        containers = generate_containers()  # deterministic default

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

    # Per-run stale override takes precedence over global
    effective_stale = _stale_overrides.get(run_id, _stale_minutes) if run_id else _stale_minutes

    # Scenario stale override (if scenario sets stale_minutes)
    if _active_scenario_id in PB12_SCENARIOS:
        sc_stale = PB12_SCENARIOS[_active_scenario_id].stale_minutes
        if sc_stale > 0:
            effective_stale = max(effective_stale, sc_stale)

    if effective_stale > 0:
        result["data_timestamp"] = (datetime.now(timezone.utc) - timedelta(minutes=effective_stale)).isoformat()
        result["data_age_minutes"] = float(effective_stale)
        result["edge_case"] = "data_staleness"
        result["edge_case_note"] = f"PPT CITOS data is {effective_stale} min old — containers may not be ready."
    else:
        result["data_timestamp"] = datetime.now(timezone.utc).isoformat()
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
    """OptETruck road ITT capacity — Tool 2 response.

    When a scenario is active, randomizes truck availability and transit time.
    """
    from app.mocks.scenarios import _active_scenario_id, _rng, PB12_SCENARIOS

    # Start with base data
    data = {
        "status": "success",
        "terminal": terminal,
        "available_trucks": TRUCK_DATA["available_trucks"],
        "total_fleet": TRUCK_DATA["total_fleet"],
        "transit_time_minutes": TRUCK_DATA["transit_time_minutes"],
        "road_conditions": TRUCK_DATA["road_conditions"].copy(),
        "cost_per_trip": TRUCK_DATA["cost_per_trip"],
        "lta_chassis_limits": TRUCK_DATA["lta_chassis_limits"],
        "estimated_round_trip_minutes": TRUCK_DATA["estimated_round_trip_minutes"],
        "earliest_departure": "2026-08-19T11:00:00+08:00",
        "latest_arrival_at_tuas": "2026-08-19T18:00:00+08:00",
    }

    # Override with scenario data if active
    if _active_scenario_id in PB12_SCENARIOS:
        sc = PB12_SCENARIOS[_active_scenario_id]
        data["available_trucks"] = sc.available_trucks.sample_int(_rng)
        data["transit_time_minutes"] = sc.transit_time_min.sample_int(_rng)
        # Recompute derived values
        data["baseline_trips_all_120_containers"] = 80  # reference only
        data["baseline_road_cost_all_120"] = 80 * COST_PARAMS["road_cost_per_trip"]
        data["capacity_ratio"] = round(data["available_trucks"] / 80, 2)

    return data


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


def get_feeder_data(feeder_id: str = "FEEDER ATLANTIC-03", run_id: str = "") -> dict:
    """PORTNET sea ITT capacity — Tool 3 response (per-run override isolated).

    When a scenario is active, randomizes feeder occupancy.
    """
    from app.mocks.scenarios import _active_scenario_id, _rng, PB12_SCENARIOS

    # Base feeder data
    base = {
        "feeder_id": feeder_id,
        "feeder_operator": FEEDER_DATA["feeder_operator"],
        "vessel_type": FEEDER_DATA["vessel_type"],
        "capacity_teu": FEEDER_DATA["capacity_teu"],
        "current_occupancy_teu": FEEDER_DATA["current_occupancy_teu"],
        "berth_status": FEEDER_DATA["berth_status"],
        "departure_window": FEEDER_DATA["departure_window"].copy(),
        "downstream_constraints": FEEDER_DATA["downstream_constraints"].copy(),
        "hold_cost_per_hour": FEEDER_DATA["hold_cost_per_hour"],
        "missed_connection_cost": FEEDER_DATA["missed_connection_cost"],
    }

    # Override with scenario data if active
    if _active_scenario_id in PB12_SCENARIOS:
        sc = PB12_SCENARIOS[_active_scenario_id]
        base["capacity_teu"] = sc.feeder_capacity_teu
        base["current_occupancy_teu"] = sc.feeder_occupancy_teu.sample_int(_rng)

    # Per-run override takes precedence
    if run_id and run_id in _overrides:
        ov = _overrides[run_id]
        base.update(ov)
        base["feeder_id"] = feeder_id

    base["available_capacity_teu"] = base["capacity_teu"] - base["current_occupancy_teu"]

    return {"status": "success", **base}


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
    """CITOS Tuas loading sequence — Tool 5 response.

    When a scenario is active, adjusts QC assignments based on container volume.
    """
    from app.mocks.scenarios import _active_scenario_id, _rng, PB12_SCENARIOS

    # Base QC assignments
    qc_assignments = [
        {"qc_id": "QC-07", "bay": "Bay14", "status": "available"},
        {"qc_id": "QC-07", "bay": "Bay12", "status": "available"},
        {"qc_id": "QC-08", "bay": "Bay10", "status": "available"},
        {"qc_id": "QC-08", "bay": "Bay08", "status": "available"},
    ]

    # High-volume scenario: activate extra QC
    if _active_scenario_id in PB12_SCENARIOS:
        sc = PB12_SCENARIOS[_active_scenario_id]
        container_count = sc.container_count.sample_int(_rng)
        if container_count > 130:
            qc_assignments.append({"qc_id": "QC-09", "bay": "Bay06", "status": "available"})

    return {
        "status": "success",
        "vessel_id": vessel_id,
        "original_loading_sequence": TUAS_YARD_DATA["original_loading_sequence"],
        "updated_loading_sequence": (
            f"Bay14(road@{itt_eta_road})→Bay12(road@{itt_eta_road})"
            f"→Bay10(sea@{itt_eta_sea})→Bay08(sea@{itt_eta_sea})"
        ),
        "qc_adjustments": [
            {"qc_id": q["qc_id"], "original_bay": q["bay"], "new_bay": q["bay"], "eta": itt_eta_road if "Bay14" in q["bay"] or "Bay12" in q["bay"] else itt_eta_sea}
            for q in qc_assignments
        ],
        "estimated_loading_completion": "2026-08-19T19:30:00+08:00",
        "margin_before_departure_minutes": 30,
    }


# ---------------------------------------------------------------------------
# Split computation (Tool 4) — internal, not a mock API
# ---------------------------------------------------------------------------

def compute_itt_split_default() -> dict:
    """Compute optimal road/sea split.

    When a scenario is active, computes from randomized data.
    Otherwise returns the classic 80/40 = $10,400 default.
    """
    from app.mocks.scenarios import _active_scenario_id, _rng, PB12_SCENARIOS

    # Get container and truck data
    container_data = get_container_data()
    truck_data = get_truck_data()

    total_containers = container_data["total_containers"]
    fortyft = container_data["container_breakdown"]["40ft_feu"]
    twentyft = container_data["container_breakdown"]["20ft_teu"]
    available_trucks = truck_data["available_trucks"]
    cost_per_trip = COST_PARAMS["road_cost_per_trip"]
    sea_handling_per = COST_PARAMS["sea_terminal_handling"]

    # Compute optimal split
    total_trips_100pct_road = fortyft + twentyft // 2
    max_road_trips = min(total_trips_100pct_road, available_trucks * 2)
    road_containers = min(total_containers, max_road_trips)
    sea_containers = total_containers - road_containers
    road_trips = fortyft + min(twentyft, road_containers - fortyft) // 2
    road_cost = road_trips * cost_per_trip
    sea_handling = sea_containers * sea_handling_per
    total_cost = road_cost + sea_handling

    # Baseline (all road)
    baseline_cost = total_trips_100pct_road * cost_per_trip

    return {
        "status": "success",
        "optimal_split": {
            "road_containers": road_containers,
            "road_breakdown": f"{fortyft}x 40ft ({fortyft} trips) + {min(twentyft, road_containers - fortyft)}x 20ft ({(min(twentyft, road_containers - fortyft)) // 2} trips)",
            "road_trips": road_trips,
            "road_cost": road_cost,
            "sea_containers": sea_containers,
            "sea_marginal_charter_cost": 0,
            "sea_terminal_handling_cost": sea_handling,
            "total_transport_cost": total_cost,
            "cost_notes": (
                "Sea transfer has $0 marginal charter cost (scheduled feeder rotation) "
                f"+ ${sea_handling:,} terminal handling (${sea_handling_per}/lift across {sea_containers} containers)"
            ),
        },
        "alternatives": [
            {
                "road_containers": min(total_containers, total_trips_100pct_road + 20),
                "road_breakdown": "100% road (overflow)",
                "road_trips": total_trips_100pct_road + 20,
                "road_cost": (total_trips_100pct_road + 20) * cost_per_trip,
                "sea_containers": 0,
                "sea_marginal_charter_cost": 0,
                "sea_terminal_handling_cost": 0,
                "total_transport_cost": (total_trips_100pct_road + 20) * cost_per_trip,
                "risk": "road_congestion_delay_near_pandan",
            },
            {
                "road_containers": max(0, total_containers - sea_containers - 20),
                "road_breakdown": "More sea, less road",
                "road_trips": max(0, total_trips_100pct_road - 20),
                "road_cost": max(0, total_trips_100pct_road - 20) * cost_per_trip,
                "sea_containers": min(total_containers, sea_containers + 20),
                "sea_marginal_charter_cost": 0,
                "sea_terminal_handling_cost": min(total_containers, sea_containers + 20) * sea_handling_per,
                "total_transport_cost": max(0, total_trips_100pct_road - 20) * cost_per_trip + min(total_containers, sea_containers + 20) * sea_handling_per,
                "risk": "feeder_capacity_exceeded",
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
            "baseline_all_road_cost": baseline_cost,
            "baseline_all_road_trips": total_trips_100pct_road,
            "optimised_transport_cost": total_cost,
            "direct_transport_savings": baseline_cost - total_cost,
        },
    }
