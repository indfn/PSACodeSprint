"""Scenario system — randomized mock data within probability distributions.

Each scenario defines distributions (mean, stddev, min, max) for key parameters.
Per-run seeding ensures variation between runs within the same scenario.

Usage:
    from app.mocks.scenarios import set_scenario, get_scenario, generate_scenario_data
    set_scenario("nominal", seed=time.time_ns())
    data = generate_scenario_data("pb-12-itt")
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Distribution helper
# ---------------------------------------------------------------------------

@dataclass
class Dist:
    """Normal distribution clamped to [lo, hi]."""
    mean: float
    std: float
    lo: float
    hi: float

    def sample(self, rng: random.Random) -> float:
        val = rng.gauss(self.mean, self.std)
        return max(self.lo, min(self.hi, val))

    def sample_int(self, rng: random.Random) -> int:
        return int(round(self.sample(rng)))


# ---------------------------------------------------------------------------
# PB-12 scenarios (ITT Coordination)
# ---------------------------------------------------------------------------

@dataclass
class PB12Scenario:
    id: str
    name: str
    description: str
    # Container distributions
    container_count: Dist = field(default_factory=lambda: Dist(120, 15, 80, 150))
    dg_count: Dist = field(default_factory=lambda: Dist(3, 1, 1, 5))
    priority_ratio: Dist = field(default_factory=lambda: Dist(0.375, 0.05, 0.25, 0.5))
    # Truck distributions — realistic: 65-80% available (rest in maintenance/off-shift)
    available_trucks: Dist = field(default_factory=lambda: Dist(40, 5, 30, 48))
    total_fleet: int = 55
    transit_time_min: Dist = field(default_factory=lambda: Dist(90, 10, 60, 120))
    # Feeder distributions
    feeder_capacity_teu: int = 800
    feeder_occupancy_teu: Dist = field(default_factory=lambda: Dist(620, 80, 400, 780))
    # Confidence
    confidence_initial: Dist = field(default_factory=lambda: Dist(0.90, 0.03, 0.85, 0.95))
    # Mutations applied during run
    mutations: list[str] = field(default_factory=list)
    # Stale data (minutes) — 0 = fresh
    stale_minutes: int = 0


PB12_SCENARIOS: dict[str, PB12Scenario] = {
    "nominal": PB12Scenario(
        id="nominal",
        name="Normal",
        description="Clean data, all systems healthy. Standard 80/40 split.",
        container_count=Dist(120, 15, 100, 140),
        available_trucks=Dist(40, 4, 34, 46),
        feeder_occupancy_teu=Dist(620, 80, 500, 750),
        confidence_initial=Dist(0.92, 0.02, 0.88, 0.95),
        mutations=[],
    ),
    "deviation": PB12Scenario(
        id="deviation",
        name="Feeder Berth Conflict",
        description="Feeder berth conflict detected during monitor check.",
        container_count=Dist(140, 10, 120, 155),
        available_trucks=Dist(38, 4, 32, 44),
        feeder_occupancy_teu=Dist(680, 50, 600, 760),
        confidence_initial=Dist(0.88, 0.02, 0.85, 0.92),
        mutations=["feeder_berth_conflict"],
    ),
    "stale": PB12Scenario(
        id="stale",
        name="Stale/Missing Data",
        description="PPT CITOS data is 25+ minutes old. Guardrails fire.",
        container_count=Dist(100, 15, 80, 120),
        available_trucks=Dist(32, 5, 25, 40),
        feeder_occupancy_teu=Dist(550, 80, 400, 650),
        confidence_initial=Dist(0.88, 0.02, 0.85, 0.92),
        mutations=["stale_data"],
        stale_minutes=25,
    ),
    "escalation": PB12Scenario(
        id="escalation",
        name="Low Trucks",
        description="Low confidence + low trucks. Triggers HITL-5 escalation.",
        container_count=Dist(150, 12, 130, 165),
        available_trucks=Dist(18, 4, 12, 24),
        feeder_occupancy_teu=Dist(720, 60, 620, 800),
        confidence_initial=Dist(0.62, 0.05, 0.52, 0.72),
        mutations=["low_trucks"],
    ),
}


# ---------------------------------------------------------------------------
# PB-01 scenarios (Berth Delay)
# ---------------------------------------------------------------------------

@dataclass
class PB01Scenario:
    id: str
    name: str
    description: str
    # Vessel
    vessel_delay_hours: Dist = field(default_factory=lambda: Dist(2, 1, 0, 6))
    vessel_draft_m: Dist = field(default_factory=lambda: Dist(14.5, 1, 12, 16))
    # Berth
    berth_occupancy: Dist = field(default_factory=lambda: Dist(0.7, 0.1, 0.4, 0.95))
    berth_count_available: Dist = field(default_factory=lambda: Dist(2, 1, 0, 3))
    # QC — realistic: 60-75% available (rest on other berths/maintenance)
    qc_available: Dist = field(default_factory=lambda: Dist(26, 3, 20, 32))
    qc_total: int = 40
    # Confidence
    confidence_initial: Dist = field(default_factory=lambda: Dist(0.90, 0.03, 0.85, 0.95))
    # Mutations
    mutations: list[str] = field(default_factory=list)


PB01_SCENARIOS: dict[str, PB01Scenario] = {
    "nominal": PB01Scenario(
        id="nominal",
        name="Nominal",
        description="Vessel on time, berth available, QC ready.",
        vessel_delay_hours=Dist(0.5, 0.3, 0, 1),
        berth_occupancy=Dist(0.6, 0.1, 0.4, 0.8),
        berth_count_available=Dist(2, 0.5, 1, 3),
        qc_available=Dist(26, 2, 22, 30),
        confidence_initial=Dist(0.93, 0.02, 0.90, 0.95),
        mutations=[],
    ),
    "conflict": PB01Scenario(
        id="conflict",
        name="Berth Conflict",
        description="Two vessels competing for same berth.",
        vessel_delay_hours=Dist(1, 0.5, 0, 2),
        berth_occupancy=Dist(0.9, 0.05, 0.85, 0.95),
        berth_count_available=Dist(0.5, 0.3, 0, 1),
        qc_available=Dist(24, 3, 18, 28),
        confidence_initial=Dist(0.82, 0.03, 0.78, 0.87),
        mutations=["berth_conflict"],
    ),
    "delay": PB01Scenario(
        id="delay",
        name="Vessel Delay",
        description="Vessel arrives 4+ hours late. Berth window at risk.",
        vessel_delay_hours=Dist(5, 1.5, 3, 8),
        berth_occupancy=Dist(0.75, 0.1, 0.5, 0.9),
        berth_count_available=Dist(1.5, 0.5, 0, 2),
        qc_available=Dist(22, 3, 16, 28),
        confidence_initial=Dist(0.78, 0.04, 0.70, 0.85),
        mutations=["vessel_delay"],
    ),
    "equipment": PB01Scenario(
        id="equipment",
        name="QC Failure",
        description="Quay crane goes down mid-operation.",
        vessel_delay_hours=Dist(1, 0.5, 0, 2),
        berth_occupancy=Dist(0.7, 0.1, 0.5, 0.85),
        berth_count_available=Dist(2, 0.5, 1, 3),
        qc_available=Dist(18, 4, 10, 24),
        confidence_initial=Dist(0.75, 0.05, 0.65, 0.82),
        mutations=["qc_failure"],
    ),
}


# ---------------------------------------------------------------------------
# Active scenario context (set per-run)
# ---------------------------------------------------------------------------

_active_scenario_id: str = ""  # empty = no scenario set, use deterministic defaults
_active_problem_id: str = "pb-12-itt"
_rng: random.Random = random.Random()


def set_scenario(problem_id: str, scenario_id: str, seed: int | None = None) -> None:
    """Set the active scenario for subsequent data generation calls."""
    global _active_scenario_id, _active_problem_id, _rng
    _active_problem_id = problem_id
    _active_scenario_id = scenario_id
    _rng = random.Random(seed or time.time_ns())


def get_scenario() -> str:
    """Get the active scenario ID."""
    return _active_scenario_id


def get_problem() -> str:
    """Get the active problem ID."""
    return _active_problem_id


def get_rng() -> random.Random:
    """Get the active RNG (for callers that need direct access)."""
    return _rng


# ---------------------------------------------------------------------------
# PB-12 data generation
# ---------------------------------------------------------------------------

def _generate_pb12_containers(count: int, dg_count: int, priority_ratio: float, rng: random.Random) -> list[dict]:
    """Generate randomized container list."""
    from app.mocks.data import CONSIGNEES, DESTINATION_PORTS, YARD_BLOCKS, _generate_container_id, _generate_yard_position

    containers = []
    high_priority_count = int(count * priority_ratio)
    dg_placed = 0

    for i in range(count):
        size = "40ft" if rng.random() < 0.33 else "20ft"
        block_idx = i % len(YARD_BLOCKS)
        yard_block, yard_position = _generate_yard_position(
            int(YARD_BLOCKS[block_idx].split("-")[1]), i
        )
        weight = rng.randint(18000, 32000) if size == "40ft" else rng.randint(8000, 18000)

        dg_class = None
        if dg_placed < dg_count and rng.random() < 0.05:
            dg_class = rng.choice(["3", "8"])
            dg_placed += 1

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

    while dg_placed < dg_count:
        idx = rng.randint(0, len(containers) - 1)
        if containers[idx]["dg_class"] is None:
            containers[idx]["dg_class"] = rng.choice(["3", "8"])
            dg_placed += 1

    return containers


def generate_pb12_data(scenario_id: str | None = None) -> dict[str, Any]:
    """Generate all PB-12 mock data for the given scenario.

    Returns dict with keys: containers, trucks, feeder, loading_sequence, split.
    """
    sid = scenario_id or _active_scenario_id
    rng = _rng

    scenarios = PB12_SCENARIOS
    if sid not in scenarios:
        sid = "nominal"
    sc = scenarios[sid]

    # Containers
    container_count = sc.container_count.sample_int(rng)
    dg_count = sc.dg_count.sample_int(rng)
    priority_ratio = sc.priority_ratio.sample(rng)
    containers = _generate_pb12_containers(container_count, dg_count, priority_ratio, rng)

    fortyft = [c for c in containers if c["size"] == "40ft"]
    twentyft = [c for c in containers if c["size"] == "20ft"]
    dg = [c for c in containers if c["dg_class"] is not None]

    seen_blocks: set[str] = set()
    blocks_affected: list[str] = []
    for c in containers:
        if c["yard_block"] not in seen_blocks:
            seen_blocks.add(c["yard_block"])
            blocks_affected.append(c["yard_block"])

    # Trucks
    available_trucks = sc.available_trucks.sample_int(rng)
    transit_time = sc.transit_time_min.sample_int(rng)

    # Feeder
    feeder_occupancy = sc.feeder_occupancy_teu.sample_int(rng)
    feeder_capacity = sc.feeder_capacity_teu
    feeder_available = max(0, feeder_capacity - feeder_occupancy)

    # Confidence
    confidence = sc.confidence_initial.sample(rng)

    # Road/sea split (computed from container + truck data)
    total_trips_road_100pct = len(fortyft) + len(twentyft) // 2
    max_road_trips = min(total_trips_road_100pct, available_trucks * 2)  # 2 TEU per truck
    road_containers = min(container_count, max_road_trips)
    sea_containers = container_count - road_containers
    road_trips = len(fortyft) + (min(len(twentyft), road_containers - len(fortyft))) // 2
    road_cost = road_trips * 150
    sea_handling = sea_containers * 35
    total_cost = road_cost + sea_handling

    return {
        "scenario": sid,
        "containers": {
            "total": container_count,
            "fortyft": len(fortyft),
            "twentyft": len(twentyft),
            "dg": len(dg),
            "blocks_affected": blocks_affected,
            "list": containers,
        },
        "trucks": {
            "available": available_trucks,
            "total_fleet": sc.total_fleet,
            "transit_time_minutes": transit_time,
            "cost_per_trip": 150,
        },
        "feeder": {
            "capacity_teu": feeder_capacity,
            "occupancy_teu": feeder_occupancy,
            "available_teu": feeder_available,
            "berth_status": "berthed_at_PPT_B12",
        },
        "split": {
            "road_containers": road_containers,
            "sea_containers": sea_containers,
            "road_trips": road_trips,
            "road_cost": road_cost,
            "sea_handling_cost": sea_handling,
            "total_cost": total_cost,
        },
        "confidence": confidence,
        "mutations": sc.mutations,
        "stale_minutes": sc.stale_minutes,
    }


# ---------------------------------------------------------------------------
# PB-01 data generation
# ---------------------------------------------------------------------------

def generate_pb01_data(scenario_id: str | None = None) -> dict[str, Any]:
    """Generate all PB-01 mock data for the given scenario.

    Returns dict with keys: vessel, berth, qc, reassignment.
    """
    sid = scenario_id or _active_scenario_id
    rng = _rng

    scenarios = PB01_SCENARIOS
    if sid not in scenarios:
        sid = "nominal"
    sc = scenarios[sid]

    # Vessel
    delay_hours = sc.vessel_delay_hours.sample(rng)
    draft = sc.vessel_draft_m.sample(rng)

    # Berth
    occupancy = sc.berth_occupancy.sample(rng)
    berths_available = sc.berth_count_available.sample_int(rng)

    # QC
    qc_available = sc.qc_available.sample_int(rng)

    # Confidence
    confidence = sc.confidence_initial.sample(rng)

    # Determine berth assignment
    if berths_available > 0:
        assigned_berth = "B-07" if berths_available >= 2 else "B-03"
        berth_status = "available"
    else:
        assigned_berth = "B-07"  # fallback
        berth_status = "conflict"

    return {
        "scenario": sid,
        "vessel": {
            "delay_hours": round(delay_hours, 1),
            "draft_m": round(draft, 1),
            "status": "delayed" if delay_hours > 2 else "approaching",
        },
        "berth": {
            "occupancy": round(occupancy, 2),
            "available_count": berths_available,
            "assigned": assigned_berth,
            "status": berth_status,
        },
        "qc": {
            "available": qc_available,
            "total": sc.qc_total,
        },
        "confidence": confidence,
        "mutations": sc.mutations,
    }


# ---------------------------------------------------------------------------
# Convenience: list available scenarios for a problem
# ---------------------------------------------------------------------------

def list_scenarios(problem_id: str) -> list[dict[str, str]]:
    """Return available scenarios for a problem ID."""
    if problem_id == "pb-12-itt":
        return [
            {"id": sc.id, "name": sc.name, "description": sc.description}
            for sc in PB12_SCENARIOS.values()
        ]
    elif problem_id == "pb-01-berth":
        return [
            {"id": sc.id, "name": sc.name, "description": sc.description}
            for sc in PB01_SCENARIOS.values()
        ]
    return [{"id": "nominal", "name": "Normal", "description": "Default scenario"}]
