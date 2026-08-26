"""
Tool 4: compute_optimal_split — Generalised Decision Engine

Multi-constraint optimisation for resource allocation across Cluster C2 problems.
Same core logic, different cost models and constraints per problem.

Receives: candidates (T1), road_capacity (T2), sea_capacity (T3)
Feeds into: HITL Gate 1 (approval card), HITL Gate 2 (dispatch)

Supports all 7 Cluster C2 problems via problem_config:
  - PB-01: Berth Delay        → berth reassignment optimisation
  - PB-02: DTQC Breakdown     → crane reallocation
  - PB-04: Missed Connection  → feeder re-routing
  - PB-09: Expressway Disruption → truck rerouting / slot reallocation
  - PB-10: Sea-Air Cut-Off    → modal shift decision
  - PB-11: Customs Hold       → document acceleration prioritisation
  - PB-12: ITT Coordination   → road/sea split (flagship)

Master Charter ref: Section 3, Tool 4
Tech Stack ref: Section 8, YAML config (tools.compute_optimal_split)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants — grounded in PSA / Singapore operational parameters
# ---------------------------------------------------------------------------

# Cost parameters (Master Charter §5)
ROAD_COST_PER_TRIP_SGD = 150          # PPT → Tuas ~35 km via WCH/AYE
SEA_TERMINAL_HANDLING_PER_LIFT = 35    # PSA standard lift cost
SEA_MARGINAL_CHARTER_COST = 0         # Scheduled feeder rotation
VESSEL_DEMURRAGE_PER_HR = 2500        # Mother vessel at Tuas
FEEDER_CHARTER_PER_HR = 800           # Feeder vessel
YARD_REHANDLE_COST = 35               # Unproductive re-handle
MISSED_CONNECTION_COST = 150           # SLA penalty per container

# LTA regulation
LTA_CHASSIS_FEU = 1    # 1x 40ft per prime mover
LTA_CHASSIS_TEU = 2    # up to 2x 20ft per prime mover

# Container mix (PB-12 default)
DEFAULT_TOTAL_CONTAINERS = 120
DEFAULT_40FT_FEU = 40
DEFAULT_20FT_TEU = 80

# Timeline
DEFAULT_VESSEL_DEPARTURE_HOUR = 20     # 20:00 local
ITT_ARRIVAL_DEADLINE_BUFFER_MIN = 60   # Must arrive 1 hr before vessel departure


# ---------------------------------------------------------------------------
# Problem configurations — one per Cluster C2 sibling problem
# ---------------------------------------------------------------------------

@dataclass
class ProblemConfig:
    """Configuration for a specific Cluster C2 problem.

    The same optimisation engine handles all 7 problems. Only the cost
    model, constraints, and decision variables change per problem.
    """

    problem_id: str
    name: str
    sector: str
    description: str

    # Decision variables (what the agent optimises over)
    decision_variables: list[str]            # e.g. ["road_containers", "sea_containers"]
    optimisation_target: str                 # "min_cost" | "min_time" | "max_throughput"

    # Cost model
    cost_params: dict[str, float]            # problem-specific cost parameters
    cost_function: str                       # name of the cost function to use

    # Constraints
    constraints: dict[str, Any]              # problem-specific constraints

    # Systems involved
    systems: list[str]                       # which PSA systems are queried

    # Tools available
    tools: list[str]                         # which tools the agent can call

    # Escalation triggers
    escalation_triggers: list[dict[str, Any]]

    # Confidence threshold
    confidence_threshold: float = 0.85

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "name": self.name,
            "sector": self.sector,
            "description": self.description,
            "decision_variables": self.decision_variables,
            "optimisation_target": self.optimisation_target,
            "cost_params": self.cost_params,
            "cost_function": self.cost_function,
            "constraints": self.constraints,
            "systems": self.systems,
            "tools": self.tools,
            "escalation_triggers": self.escalation_triggers,
            "confidence_threshold": self.confidence_threshold,
        }


# --- PB-12: ITT Coordination (Flagship) ---
PB_12_CONFIG = ProblemConfig(
    problem_id="PB-12",
    name="Multi-Party ITT Coordination Failure",
    sector="Multimodal Logistics",
    description="Move 120 containers PPT→Tuas, optimise road/sea split",
    decision_variables=["road_containers", "sea_containers"],
    optimisation_target="min_cost",
    cost_params={
        "road_cost_per_trip": 150,
        "sea_handling_per_lift": 35,
        "sea_marginal_charter": 0,
        "vessel_demurrage_per_hr": 2500,
        "feeder_charter_per_hr": 800,
        "yard_rehandle": 35,
        "missed_connection": 150,
        "staff_hourly": 50,
    },
    cost_function="itt_split",
    constraints={
        "lta_chassis": "1x 40ft (FEU) OR up to 2x 20ft (TEU) per prime mover",
        "feeder_available_teu": 40,
        "feeder_loading_rate_per_hr": 20,
        "feeder_max_loading_hours": 4,
        "max_road_trips_per_wave": 20,
        "peak_hours": ["07:30-09:30", "17:30-19:30"],
        "transit_off_peak_min": 45,
        "transit_peak_min": 95,
        "itt_arrival_buffer_min": 60,
    },
    systems=["citos_ppt", "citos_tuas", "optetruck", "feeder", "portnet"],
    tools=[
        "query_container_readiness",
        "check_road_itt_capacity",
        "check_sea_itt_capacity",
        "compute_optimal_split",
        "update_tuas_loading_sequence",
        "receive_webhook",
    ],
    escalation_triggers=[
        {"id": "esc_1", "name": "Low confidence", "threshold": 0.85},
        {"id": "esc_2", "name": "Feeder hold > 1.5 hrs", "threshold": 1.5},
        {"id": "esc_3", "name": "Cost > $10,000", "threshold": 10000},
        {"id": "esc_4", "name": "Data age > 30 min", "threshold": 30},
        {"id": "esc_5", "name": "Trucks < 60% required", "threshold": 0.6},
        {"id": "esc_6", "name": "Feeder response > 15 min", "threshold": 15},
        {"id": "esc_7", "name": "Planner conflict", "threshold": None},
    ],
)


# --- PB-01: Berth Delay ---
PB_01_CONFIG = ProblemConfig(
    problem_id="PB-01",
    name="Berth Delay Cascade",
    sector="Berth & Marine",
    description="Reassign berths when vessel arrives late, minimise DTQC idle time",
    decision_variables=["berth_assignment", "qc_reallocation"],
    optimisation_target="min_cost",
    cost_params={
        "vessel_demurrage_per_hr": 2500,
        "berth_idle_cost_per_hr": 500,
        "qc_repositioning_cost": 2000,
        "pilot_standby_per_hr": 300,
        "tidal_window_miss_cost": 5000,
    },
    cost_function="berth_reassignment",
    constraints={
        "max_berths": 56,
        "min_qc_per_berth": 2,
        "max_qc_per_berth": 4,
        "tidal_windows": ["spring", "neap"],
        "pilot_availability": True,
        "berth_draft_limits": {"A": 16.5, "B": 15.0, "C": 14.0},
    },
    systems=["vtis", "optevoyage", "citos_ppt"],
    tools=[
        "query_vessel_arrival",
        "check_berth_availability",
        "check_qc_availability",
        "compute_berth_reassignment",
        "notify_vessel_operator",
    ],
    escalation_triggers=[
        {"id": "esc_1", "name": "Low confidence", "threshold": 0.85},
        {"id": "esc_2", "name": "Demurrage > $10,000", "threshold": 10000},
        {"id": "esc_3", "name": "Tidal window miss", "threshold": None},
    ],
)


# --- PB-02: DTQC Breakdown ---
PB_02_CONFIG = ProblemConfig(
    problem_id="PB-02",
    name="DTQC Breakdown Cascade",
    sector="Container Yard & Internal Transport",
    description="Reallocate cranes when a quay crane breaks down mid-operations",
    decision_variables=["crane_reallocation", "berth_sequence"],
    optimisation_target="min_cost",
    cost_params={
        "vessel_demurrage_per_hr": 2500,
        "crane_rental_per_hr": 800,
        "container_delay_per_teu": 25,
        "overtime_labour_per_hr": 75,
        "yard_congestion_per_hr": 500,
    },
    cost_function="crane_reallocation",
    constraints={
        "max_dtqc": 12,
        "min_operational_dtqc": 8,
        "crane_repositioning_time_min": 30,
        "max_container_throughput_per_qc_per_hr": 30,
        "overtime_limit_hours": 4,
    },
    systems=["rocc", "citos_ppt", "fms"],
    tools=[
        "query_crane_status",
        "check_container_backlog",
        "compute_crane_reallocation",
        "notify_yard_planner",
        "request_emergency_crane",
    ],
    escalation_triggers=[
        {"id": "esc_1", "name": "Low confidence", "threshold": 0.85},
        {"id": "esc_2", "name": "Operational QC < 8", "threshold": 8},
        {"id": "esc_3", "name": "Backlog > 200 TEU", "threshold": 200},
    ],
)


# --- PB-04: Missed Feeder Connection ---
PB_04_CONFIG = ProblemConfig(
    problem_id="PB-04",
    name="Missed Feeder Connection",
    sector="Multimodal Logistics",
    description="Reroute containers when feeder misses connection at downstream port",
    decision_variables=["reroute_option", "priority_containers"],
    optimisation_target="min_cost",
    cost_params={
        "missed_connection_per_container": 150,
        "reroute_cost_per_container": 200,
        "storage_per_day": 45,
        "downstream_demurrage_per_hr": 100,
        "sla_penalty_per_container": 250,
    },
    cost_function="feeder_reroute",
    constraints={
        "max_reroute_containers": 60,
        "reroute_deadline_hours": 24,
        "available_reroute_vessels": 3,
        "priority_sla_containers": 20,
    },
    systems=["portnet", "citos_ppt", "citos_tuas"],
    tools=[
        "query_feeder_status",
        "check_reroute_options",
        "compute_reroute_plan",
        "notify_consignee",
        "update_loading_sequence",
    ],
    escalation_triggers=[
        {"id": "esc_1", "name": "Low confidence", "threshold": 0.85},
        {"id": "esc_2", "name": "Reroute cost > $20,000", "threshold": 20000},
        {"id": "esc_3", "name": "SLA breach imminent", "threshold": None},
    ],
)


# --- PB-09: Expressway Disruption ---
PB_09_CONFIG = ProblemConfig(
    problem_id="PB-09",
    name="Expressway Disruption Gridlock",
    sector="Gate & External Haulage",
    description="Reroute trucks when AYE/ECP is blocked, reallocate time slots",
    decision_variables=["truck_reroute", "slot_reallocation"],
    optimisation_target="min_time",
    cost_params={
        "truck_delay_per_hr": 50,
        "slot_waste_cost": 100,
        "fuel_detour_per_trip": 30,
        "driver_overtime_per_hr": 75,
        "gate_congestion_per_hr": 200,
    },
    cost_function="truck_reroute",
    constraints={
        "max_detour_time_min": 30,
        "alternate_routes": ["TPE", "BKE", "PIE"],
        "max_simultaneous_trucks": 20,
        "slot_realloc_window_min": 60,
    },
    systems=["optetruck", "smartbooking", "ibox"],
    tools=[
        "query_traffic_status",
        "check_alternate_routes",
        "compute_reroute_plan",
        "reallocate_time_slots",
        "notify_gate_operations",
    ],
    escalation_triggers=[
        {"id": "esc_1", "name": "Low confidence", "threshold": 0.85},
        {"id": "esc_2", "name": "Detour > 30 min", "threshold": 30},
        {"id": "esc_3", "name": "Gate backlog > 50 trucks", "threshold": 50},
    ],
)


# --- PB-10: Sea-Air Cut-Off ---
PB_10_CONFIG = ProblemConfig(
    problem_id="PB-10",
    name="Sea-Air Cut-Off Breach",
    sector="Multimodal Logistics",
    description="Decide modal shift when sea cut-off is missed for air cargo handover",
    decision_variables=["modal_shift", "priority_allocation"],
    optimisation_target="min_cost",
    cost_params={
        "air_freight_per_kg": 4.50,
        "sea_freight_per_teu": 800,
        "cut_off_breach_penalty": 2000,
        "storage_per_day": 60,
        "customs_expediting": 500,
    },
    cost_function="modal_shift",
    constraints={
        "max_air_capacity_kg": 50000,
        "air_cut_off_hours": 6,
        "sea_cut_off_hours": 2,
        "customs_processing_min": 45,
    },
    systems=["optemodal", "tradenet", "sats"],
    tools=[
        "query_cargo_status",
        "check_air_availability",
        "compute_modal_shift",
        "expedite_customs",
        "notify_shipper",
    ],
    escalation_triggers=[
        {"id": "esc_1", "name": "Low confidence", "threshold": 0.85},
        {"id": "esc_2", "name": "Air cost > $50,000", "threshold": 50000},
        {"id": "esc_3", "name": "Customs delay > 1 hr", "threshold": 60},
    ],
)


# --- PB-11: Customs Hold ---
PB_11_CONFIG = ProblemConfig(
    problem_id="PB-11",
    name="Customs Hold Gridlock",
    sector="Multimodal Logistics",
    description="Prioritise document acceleration when multiple containers are held by customs",
    decision_variables=["document_priority", "container_sequence"],
    optimisation_target="min_time",
    cost_params={
        "storage_per_day": 45,
        "demurrage_per_container_per_day": 100,
        "document_expediting_cost": 200,
        "staff_overtime_per_hr": 75,
        "reputation_cost_per_delay": 500,
    },
    cost_function="document_prioritisation",
    constraints={
        "max_held_containers": 30,
        "customs_processing_hours": 8,
        "document_types": ["BL", "CO", "invoice", "packing_list"],
        "expedite_available": True,
    },
    systems=["tradenet", "calista", "portnet"],
    tools=[
        "query_customs_hold",
        "check_document_status",
        "compute_priority_sequence",
        "expedite_documents",
        "notify_consignee",
    ],
    escalation_triggers=[
        {"id": "esc_1", "name": "Low confidence", "threshold": 0.85},
        {"id": "esc_2", "name": "Held containers > 20", "threshold": 20},
        {"id": "esc_3", "name": "Storage cost > $10,000", "threshold": 10000},
    ],
)


# --- Config registry ---
PROBLEM_CONFIGS: dict[str, ProblemConfig] = {
    "PB-01": PB_01_CONFIG,
    "PB-02": PB_02_CONFIG,
    "PB-04": PB_04_CONFIG,
    "PB-09": PB_09_CONFIG,
    "PB-10": PB_10_CONFIG,
    "PB-11": PB_11_CONFIG,
    "PB-12": PB_12_CONFIG,
}


def load_problem_config(problem_id: str) -> ProblemConfig:
    """Load problem configuration by ID.

    Args:
        problem_id: e.g. "PB-12", "PB-01", etc.

    Returns:
        ProblemConfig for the specified problem.

    Raises:
        ValueError: If problem_id is not in the registry.
    """
    if problem_id not in PROBLEM_CONFIGS:
        raise ValueError(
            f"Unknown problem '{problem_id}'. Available: {list(PROBLEM_CONFIGS.keys())}"
        )
    return PROBLEM_CONFIGS[problem_id]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ContainerCandidate:
    """Single container ready for ITT transfer (from Tool 1)."""

    container_id: str
    size: str          # "40ft" or "20ft"
    yard_block: str
    weight_kg: float
    dg_class: str | None
    priority: str      # "high" or "standard"
    ready_for_itt: bool


@dataclass
class SplitOption:
    """A single road/sea split candidate."""

    road_containers: int
    road_40ft: int
    road_20ft: int
    sea_containers: int
    sea_40ft: int
    sea_20ft: int
    road_trips: int
    road_cost: int
    sea_handling_cost: int
    sea_charter_cost: int
    total_transport_cost: int
    risk: str
    feasible: bool
    infeasibility_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "road_containers": self.road_containers,
            "road_breakdown": (
                f"{self.road_40ft}x 40ft ({self.road_40ft} trips) + "
                f"{self.road_20ft}x 20ft ({(self.road_20ft + 1) // 2} trips)"
            ),
            "road_trips": self.road_trips,
            "road_cost": self.road_cost,
            "sea_containers": self.sea_containers,
            "sea_breakdown": (
                f"{self.sea_40ft}x 40ft + {self.sea_20ft}x 20ft ({self.sea_containers} TEU)"
                if self.sea_containers > 0 else "none"
            ),
            "sea_marginal_charter_cost": self.sea_charter_cost,
            "sea_terminal_handling_cost": self.sea_handling_cost,
            "total_transport_cost": self.total_transport_cost,
            "risk": self.risk,
            "feasible": self.feasible,
            "infeasibility_reason": self.infeasibility_reason,
        }


@dataclass
class ITTSplitResult:
    """Complete ITT split optimisation result."""

    optimal_split: SplitOption
    alternatives: list[SplitOption]
    timeline: dict[str, Any]
    cost_vs_baseline: dict[str, Any]
    confidence: float
    constraint_violations: list[str]
    escalation_flags: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "success",
            "optimal_split": self.optimal_split.to_dict(),
            "alternatives": [a.to_dict() for a in self.alternatives],
            "timeline": self.timeline,
            "cost_vs_baseline": self.cost_vs_baseline,
            "confidence": self.confidence,
            "constraint_violations": self.constraint_violations,
            "escalation_flags": self.escalation_flags,
        }


# ---------------------------------------------------------------------------
# Core computation helpers (deterministic — no LLM needed)
# ---------------------------------------------------------------------------

def _compute_road_trips(feu: int, teu: int) -> int:
    """Compute LTA-compliant road trips for given container mix.

    LTA rule: 1x 40ft (FEU) per prime mover, OR up to 2x 20ft (TEU).
    40ft: 1 trip each. 20ft: paired (2 per trip), +1 if odd.
    """
    trips_40ft = feu
    trips_20ft = (teu + 1) // 2
    return trips_40ft + trips_20ft


def _compute_road_cost(trips: int) -> int:
    return trips * ROAD_COST_PER_TRIP_SGD


def _compute_sea_handling(containers: int) -> int:
    return containers * SEA_TERMINAL_HANDLING_PER_LIFT


def _compute_timeline(
    road_trips: int,
    available_trucks: int,
    transit_time_min: int,
    sea_containers: int,
    feeder_departure: datetime,
    vessel_departure: datetime,
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    """Compute estimated arrival times for road and sea ITT.

    Args:
        reference_time: Anchor time for "now". Defaults to current time.
            Pass a fixed time for deterministic tests/replays.
    """
    tz = vessel_departure.tzinfo
    now = reference_time or (datetime.now(tz) if tz else datetime.now())

    # Road: waves of truck dispatches
    waves = 0
    if available_trucks > 0 and road_trips > 0:
        waves = math.ceil(road_trips / available_trucks)
        road_duration_min = waves * (transit_time_min * 2 + 30)  # round trip + loading
    else:
        road_duration_min = 0

    road_arrival = now + timedelta(minutes=road_duration_min)
    sea_arrival = feeder_departure + timedelta(hours=2)  # Feeder transit ~2 hrs

    loading_start = max(road_arrival, sea_arrival)
    margin_min = int((vessel_departure - loading_start).total_seconds() / 60)

    return {
        "road_itt_arrival": road_arrival.isoformat(),
        "sea_itt_arrival": sea_arrival.isoformat(),
        "tuas_loading_start": loading_start.isoformat(),
        "vessel_departure": vessel_departure.isoformat(),
        "margin_minutes": margin_min,
        "road_waves": waves if available_trucks > 0 else 0,
        "road_duration_minutes": road_duration_min,
    }


def _evaluate_risk(
    road_trips: int,
    available_trucks: int,
    transit_time_min: int,
    vessel_departure: datetime,
    road_arrival: datetime,
) -> str:
    """Evaluate risk level of a split option."""
    # Risk: road congestion or insufficient margin
    margin_min = int((vessel_departure - road_arrival).total_seconds() / 60)

    if margin_min < 30:
        return "critical_margin"
    if road_trips > available_trucks * 3:
        return "road_congestion_delay"
    if transit_time_min > 70:
        return "transit_time_high"
    return "low"


def _compute_confidence(
    optimal: SplitOption,
    available_trucks: int,
    feeder_available_teu: int,
    margin_min: int,
) -> float:
    """Compute agent confidence score for the optimal split.

    Factors:
    - Feasibility of optimal split
    - Margin before vessel departure
    - Truck availability vs demand
    - Feeder capacity headroom
    """
    score = 1.0

    if not optimal.feasible:
        score -= 0.3

    if margin_min < 60:
        score -= 0.15
    elif margin_min < 120:
        score -= 0.05

    truck_ratio = available_trucks / max(optimal.road_trips, 1)
    if truck_ratio < 0.5:
        score -= 0.2
    elif truck_ratio < 0.8:
        score -= 0.1

    feeder_headroom = feeder_available_teu - optimal.sea_containers
    if feeder_headroom < 0:
        score -= 0.25
    elif feeder_headroom < 20:
        score -= 0.05

    return round(max(score, 0.0), 2)


# ---------------------------------------------------------------------------
# Main tool function
# ---------------------------------------------------------------------------

def compute_optimal_split(
    problem_id: str = "PB-12",
    problem_config: ProblemConfig | None = None,
    candidates: list[dict[str, Any]] | None = None,
    road_capacity: dict[str, Any] | None = None,
    sea_capacity: dict[str, Any] | None = None,
    tuas_vessel_departure: str | None = None,
    constraints: dict[str, Any] | None = None,
    # Direct params for standalone usage (override candidates/capacity dicts)
    total_containers: int = DEFAULT_TOTAL_CONTAINERS,
    container_40ft: int = DEFAULT_40FT_FEU,
    container_20ft: int = DEFAULT_20FT_TEU,
    available_trucks: int = 20,
    transit_time_min: int = 45,
    feeder_available_teu: int = 180,
    feeder_departure: str | None = None,
) -> dict[str, Any]:
    """Compute optimal resource allocation for any Cluster C2 problem.

    Same core optimisation engine, different cost models per problem.
    For PB-12 (ITT Coordination): computes road/sea container split.
    For PB-01 (Berth Delay): computes berth reassignment.
    For PB-02 (DTQC): computes crane reallocation.
    etc.

    Args:
        problem_id: Problem identifier (e.g. "PB-12"). Used to load config.
        problem_config: Optional ProblemConfig override (overrides problem_id).
        candidates: Container list from Tool 1 (optional if using direct params).
        road_capacity: Road ITT capacity from Tool 2 (optional if using direct params).
        sea_capacity: Sea ITT capacity from Tool 3 (optional if using direct params).
        tuas_vessel_departure: ISO-8601 vessel departure time at Tuas.
        constraints: Extra constraints dict (optional, merged with problem config).
        total_containers: Total containers to move (default 120).
        container_40ft: Number of 40ft containers (default 40).
        container_20ft: Number of 20ft containers (default 80).
        available_trucks: Available prime movers (default 20).
        transit_time_min: Transit time PPT→Tuas in minutes (default 45).
        feeder_available_teu: Feeder vessel available capacity (default 180).
        feeder_departure: ISO-8601 feeder departure time.

    Returns:
        dict with status, optimal_split, alternatives, timeline,
        cost_vs_baseline, confidence, constraint_violations, escalation_flags.
    """
    # Load problem config
    if problem_config is None:
        problem_config = load_problem_config(problem_id)

    logger.info(
        "compute_optimal_split called: problem=%s (%s), %d containers "
        "(%dx 40ft + %dx 20ft), trucks=%d, feeder=%d TEU",
        problem_config.problem_id, problem_config.name,
        total_containers, container_40ft, container_20ft,
        available_trucks, feeder_available_teu,
    )

    # ------------------------------------------------------------------
    # 1. Parse inputs from upstream tools (if provided as dicts)
    # ------------------------------------------------------------------
    if candidates and isinstance(candidates, list) and len(candidates) > 0:
        container_40ft = sum(1 for c in candidates if c.get("size") == "40ft")
        container_20ft = sum(1 for c in candidates if c.get("size") == "20ft")
        total_containers = len(candidates)

    if road_capacity and isinstance(road_capacity, dict):
        available_trucks = road_capacity.get("available_trucks", available_trucks)
        transit_time_min = road_capacity.get("transit_time_minutes", transit_time_min)

    if sea_capacity and isinstance(sea_capacity, dict):
        feeder_available_teu = sea_capacity.get("available_capacity_teu", feeder_available_teu)
        if not feeder_departure:
            dep = sea_capacity.get("departure_window", {})
            feeder_departure = dep.get("requested") or dep.get("earliest")

    # Merge constraints from problem config
    pc_constraints = problem_config.constraints
    if constraints:
        pc_constraints = {**pc_constraints, **constraints}

    # Use config defaults if not overridden
    feeder_available_teu = pc_constraints.get("feeder_available_teu_override", feeder_available_teu)

    # Parse vessel departure
    vessel_departure_str = tuas_vessel_departure or "2026-08-19T20:00:00+08:00"
    vessel_departure = datetime.fromisoformat(vessel_departure_str)

    # Parse feeder departure
    if feeder_departure:
        feeder_dep = datetime.fromisoformat(feeder_departure)
    else:
        feeder_dep = vessel_departure - timedelta(hours=6)

    # ------------------------------------------------------------------
    # 2. Enumerate all valid splits
    # ------------------------------------------------------------------
    all_splits: list[SplitOption] = []
    constraint_violations: list[str] = []

    # Feeder capacity constraint — practical limit
    # The feeder has limited time at PPT: arrives, unloads, loads, departs.
    # Loading rate and max hours read from config (PB-12: 20/hr, 4 hrs)
    FEEDER_LOADING_RATE_PER_HR = pc_constraints.get("feeder_loading_rate_per_hr", 20)
    FEEDER_MAX_LOADING_HOURS = pc_constraints.get("feeder_max_loading_hours", 4)
    ref_tz = vessel_departure.tzinfo or feeder_dep.tzinfo
    now_ref = datetime.now(ref_tz) if ref_tz else datetime.now()
    feeder_hours_available = min(
        FEEDER_MAX_LOADING_HOURS,
        max(0, (feeder_dep - now_ref).total_seconds() / 3600),
    )
    max_sea_by_loading = int(feeder_hours_available * FEEDER_LOADING_RATE_PER_HR)

    # Practical feeder capacity: not all TEU available for this ITT
    # Feeder already carries cargo for other destinations (Port Klang, etc.)
    # Only ~40 TEU available for PPT→Tuas ITT (matching Master Charter §3 Tool 3)
    FEEDER_AVAILABLE_FOR_ITT_TEU = pc_constraints.get("feeder_available_teu", 40)
    max_sea_teu = min(
        feeder_available_teu,
        FEEDER_AVAILABLE_FOR_ITT_TEU,
        max_sea_by_loading,
    )

    logger.info(
        "Feeder constraints: available_teu=%d, loading_capacity=%d, "
        "effective_max=%d (hours=%.1f)",
        feeder_available_teu, max_sea_by_loading, max_sea_teu, feeder_hours_available,
    )

    for sea_40ft in range(0, min(container_40ft, max_sea_teu) + 1):
        for sea_20ft in range(0, min(container_20ft, max_sea_teu - sea_40ft) + 1):
            sea_containers = sea_40ft + sea_20ft
            if sea_containers == 0 and (container_40ft + container_20ft) > 0:
                # Skip all-road (baseline, not an optimised option)
                # Actually include it for comparison
                pass

            road_40ft = container_40ft - sea_40ft
            road_20ft = container_20ft - sea_20ft
            road_containers = road_40ft + road_20ft
            road_trips = _compute_road_trips(road_40ft, road_20ft)

            # Feasibility checks
            feasible = True
            reason = ""

            # Truck availability
            if road_trips > available_trucks * 4:
                # Would need >4 waves — impractical
                feasible = False
                reason = f"road_trips ({road_trips}) exceeds practical limit ({available_trucks * 4} max waves)"

            # Feeder capacity
            if sea_containers > feeder_available_teu:
                feasible = False
                reason = f"sea_containers ({sea_containers}) > feeder capacity ({feeder_available_teu} TEU)"

            # Cost computation
            road_cost = _compute_road_cost(road_trips)
            sea_handling = _compute_sea_handling(sea_containers)
            total_cost = road_cost + sea_handling

            # Risk assessment
            timeline = _compute_timeline(
                road_trips, available_trucks, transit_time_min,
                sea_containers, feeder_dep, vessel_departure,
            )
            risk = _evaluate_risk(
                road_trips, available_trucks, transit_time_min,
                vessel_departure,
                datetime.fromisoformat(timeline["road_itt_arrival"]),
            )

            # Margin check
            margin = timeline["margin_minutes"]
            if margin < 0:
                feasible = False
                reason = f"negative margin ({margin} min) — ITT arrives after vessel departure"
            elif margin < 30:
                risk = "critical_margin"

            split = SplitOption(
                road_containers=road_containers,
                road_40ft=road_40ft,
                road_20ft=road_20ft,
                sea_containers=sea_containers,
                sea_40ft=sea_40ft,
                sea_20ft=sea_20ft,
                road_trips=road_trips,
                road_cost=road_cost,
                sea_handling_cost=sea_handling,
                sea_charter_cost=SEA_MARGINAL_CHARTER_COST,
                total_transport_cost=total_cost,
                risk=risk,
                feasible=feasible,
                infeasibility_reason=reason,
            )

            all_splits.append(split)

    # ------------------------------------------------------------------
    # 3. Select optimal (minimum cost among feasible splits)
    # ------------------------------------------------------------------
    feasible_splits = [s for s in all_splits if s.feasible]
    if not feasible_splits:
        constraint_violations.append("No feasible split found — all options violate constraints")
        # Return best infeasible option
        best = min(all_splits, key=lambda s: s.total_transport_cost)
        return {
            "status": "error",
            "error": "No feasible split found",
            "best_infeasible": best.to_dict(),
            "constraint_violations": constraint_violations,
        }

    feasible_splits.sort(key=lambda s: (s.total_transport_cost, -s.road_containers))
    optimal = feasible_splits[0]

    # ------------------------------------------------------------------
    # 4. Generate alternatives (top 3 after optimal)
    # ------------------------------------------------------------------
    alternatives = feasible_splits[1:4]

    # ------------------------------------------------------------------
    # 5. Compute timeline for optimal
    # ------------------------------------------------------------------
    timeline = _compute_timeline(
        optimal.road_trips, available_trucks, transit_time_min,
        optimal.sea_containers, feeder_dep, vessel_departure,
    )

    # ------------------------------------------------------------------
    # 6. Cost vs baseline
    # ------------------------------------------------------------------
    baseline_trips = _compute_road_trips(container_40ft, container_20ft)
    baseline_cost = _compute_road_cost(baseline_trips)

    cost_vs_baseline = {
        "baseline_all_road_cost": baseline_cost,
        "baseline_all_road_trips": baseline_trips,
        "optimised_transport_cost": optimal.total_transport_cost,
        "direct_transport_savings": baseline_cost - optimal.total_transport_cost,
        "congestion_and_delay_risk_reduction": (
            "High" if optimal.road_trips < baseline_trips * 0.75
            else "Moderate" if optimal.road_trips < baseline_trips * 0.9
            else "Low"
        ),
    }

    # ------------------------------------------------------------------
    # 7. Confidence score
    # ------------------------------------------------------------------
    confidence = _compute_confidence(
        optimal, available_trucks, feeder_available_teu, timeline["margin_minutes"],
    )

    # ------------------------------------------------------------------
    # 8. Escalation flags
    # ------------------------------------------------------------------
    escalation_flags = []

    if confidence < 0.85:
        escalation_flags.append({
            "trigger_id": "esc_1",
            "name": "Low model confidence",
            "condition": f"confidence ({confidence}) < 0.85",
            "threshold": 0.85,
            "actual": confidence,
            "rationale": "Agent uncertain about optimal split — requires senior judgment",
        })

    # esc_2: Feeder hold > 1.5 hrs
    if timeline["margin_minutes"] > 0:
        estimated_feeder_hold_min = max(0, timeline["margin_minutes"] - 60)
        if estimated_feeder_hold_min > 90:
            escalation_flags.append({
                "trigger_id": "esc_2",
                "name": "Feeder hold exceeds threshold",
                "condition": f"feeder_hold ({estimated_feeder_hold_min} min) > 90 min",
                "threshold": 90,
                "actual": estimated_feeder_hold_min,
                "rationale": "Feeder must wait too long for road ITT — consider increasing sea split",
            })

    # esc_3: Total transport cost > $10,000 (or problem-specific threshold)
    cost_limit = 10000
    for trig in problem_config.escalation_triggers:
        if trig.get("id") == "esc_3" and trig.get("threshold") is not None:
            cost_limit = trig["threshold"]
            break
    if optimal.total_transport_cost > cost_limit:
        escalation_flags.append({
            "trigger_id": "esc_3",
            "name": "Total transport cost exceeds limit",
            "condition": f"total_cost (${optimal.total_transport_cost}) > ${cost_limit}",
            "threshold": cost_limit,
            "actual": optimal.total_transport_cost,
            "rationale": "Transport cost exceeds threshold — requires cost optimisation review",
        })

    # esc_4: Data age > 30 min
    data_age_threshold = 30
    for trig in problem_config.escalation_triggers:
        if trig.get("id") == "esc_4":
            data_age_threshold = trig.get("threshold", 30)
            break
    # Data age is checked at runtime (not here), but flag if margin implies stale data risk
    if timeline["margin_minutes"] < data_age_threshold:
        escalation_flags.append({
            "trigger_id": "esc_4",
            "name": "Data freshness risk — margin below data age threshold",
            "condition": f"margin ({timeline['margin_minutes']} min) < data_age_threshold ({data_age_threshold} min)",
            "threshold": data_age_threshold,
            "actual": timeline["margin_minutes"],
            "rationale": "Insufficient margin to absorb data latency — decision may be based on stale state",
        })

    # esc_5: Trucks < 60% required
    if optimal.road_trips > available_trucks * 2:
        escalation_flags.append({
            "trigger_id": "esc_5",
            "name": "Road ITT capacity below threshold",
            "condition": f"road_trips ({optimal.road_trips}) > trucks ({available_trucks}) * 2",
            "threshold": 0.5,
            "actual": round(optimal.road_trips / max(available_trucks, 1), 2),
            "rationale": "Many waves required — risk of road ITT delay",
        })

    # ------------------------------------------------------------------
    # 9. Build result
    # ------------------------------------------------------------------
    result = ITTSplitResult(
        optimal_split=optimal,
        alternatives=alternatives,
        timeline=timeline,
        cost_vs_baseline=cost_vs_baseline,
        confidence=confidence,
        constraint_violations=constraint_violations,
        escalation_flags=escalation_flags,
    )

    output = result.to_dict()
    output["problem_config"] = problem_config.to_dict()

    logger.info(
        "compute_optimal_split result [%s]: optimal=%d road / %d sea ($%d), "
        "confidence=%.2f, margin=%d min, %d alternatives",
        problem_config.problem_id,
        optimal.road_containers, optimal.sea_containers,
        optimal.total_transport_cost, confidence,
        timeline["margin_minutes"], len(alternatives),
    )

    return output


# Backward-compatible alias
compute_itt_split = compute_optimal_split


# ---------------------------------------------------------------------------
# Tool schema (for LLM function-calling)
# ---------------------------------------------------------------------------

COMPUTE_OPTIMAL_SPLIT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "compute_optimal_split",
        "description": (
            "Compute optimal resource allocation for any Cluster C2 problem. "
            "For PB-12 (ITT Coordination): road/sea container split. "
            "For PB-01 (Berth Delay): berth reassignment. "
            "For PB-02 (DTQC): crane reallocation. "
            "Returns optimal split with alternatives, cost analysis, and confidence score."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "problem_id": {
                    "type": "string",
                    "description": "Problem ID (e.g. PB-12, PB-01, PB-02)",
                    "enum": ["PB-01", "PB-02", "PB-04", "PB-09", "PB-10", "PB-11", "PB-12"],
                    "default": "PB-12",
                },
                "total_containers": {
                    "type": "integer",
                    "description": "Total containers to move (default 120)",
                    "default": 120,
                },
                "container_40ft": {
                    "type": "integer",
                    "description": "Number of 40ft (FEU) containers (default 40)",
                    "default": 40,
                },
                "container_20ft": {
                    "type": "integer",
                    "description": "Number of 20ft (TEU) containers (default 80)",
                    "default": 80,
                },
                "available_trucks": {
                    "type": "integer",
                    "description": "Available prime movers from OptETruck (default 20)",
                    "default": 20,
                },
                "transit_time_min": {
                    "type": "integer",
                    "description": "Transit time PPT→Tuas in minutes (default 45)",
                    "default": 45,
                },
                "feeder_available_teu": {
                    "type": "integer",
                    "description": "Feeder vessel available capacity in TEU (default 180)",
                    "default": 180,
                },
                "tuas_vessel_departure": {
                    "type": "string",
                    "description": "ISO-8601 vessel departure time at Tuas",
                    "default": "2026-08-19T20:00:00+08:00",
                },
                "feeder_departure": {
                    "type": "string",
                    "description": "ISO-8601 feeder departure time (optional)",
                },
            },
            "required": [],
        },
    },
}

# Backward-compatible alias
COMPUTE_ITT_SPLIT_SCHEMA = COMPUTE_OPTIMAL_SPLIT_SCHEMA


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("=== Tool 4: compute_optimal_split — Standalone Test ===\n")

    # Use a future date for testing (next day at 20:00 SGT)
    from datetime import timezone, timedelta as td
    sgt = timezone(td(hours=8))
    now = datetime.now(sgt)
    test_departure = now.replace(hour=20, minute=0, second=0, microsecond=0) + td(days=1)
    test_feeder_dep = test_departure - td(hours=6)

    # Test PB-12 (ITT Coordination — flagship)
    print("--- PB-12: ITT Coordination ---")
    result = compute_optimal_split(
        problem_id="PB-12",
        total_containers=120,
        container_40ft=40,
        container_20ft=80,
        available_trucks=20,
        transit_time_min=45,
        feeder_available_teu=180,
        tuas_vessel_departure=test_departure.isoformat(),
        feeder_departure=test_feeder_dep.isoformat(),
    )
    print(f"Optimal: {result['optimal_split']['road_containers']} road / "
          f"{result['optimal_split']['sea_containers']} sea = "
          f"${result['optimal_split']['total_transport_cost']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Alternatives: {len(result['alternatives'])}")
    print(f"Escalation flags: {len(result['escalation_flags'])}")

    # Test PB-01 (Berth Delay)
    print("\n--- PB-01: Berth Delay ---")
    result_01 = compute_optimal_split(
        problem_id="PB-01",
        total_containers=120,
        container_40ft=40,
        container_20ft=80,
        available_trucks=20,
        transit_time_min=45,
        feeder_available_teu=180,
        tuas_vessel_departure=test_departure.isoformat(),
        feeder_departure=test_feeder_dep.isoformat(),
    )
    print(f"Config: {result_01['problem_config']['name']}")
    print(f"Systems: {result_01['problem_config']['systems']}")

    # Test PB-09 (Expressway Disruption)
    print("\n--- PB-09: Expressway Disruption ---")
    result_09 = compute_optimal_split(
        problem_id="PB-09",
        total_containers=120,
        container_40ft=40,
        container_20ft=80,
        available_trucks=20,
        transit_time_min=45,
        feeder_available_teu=180,
        tuas_vessel_departure=test_departure.isoformat(),
        feeder_departure=test_feeder_dep.isoformat(),
    )
    print(f"Config: {result_09['problem_config']['name']}")
    print(f"Cost params: {result_09['problem_config']['cost_params']}")

    print("\n=== All 7 problem configs loaded ===")
    for pid in ["PB-01", "PB-02", "PB-04", "PB-09", "PB-10", "PB-11", "PB-12"]:
        cfg = load_problem_config(pid)
        print(f"  {pid}: {cfg.name} ({cfg.sector}) — {len(cfg.tools)} tools")
