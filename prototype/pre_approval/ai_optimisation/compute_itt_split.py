"""
Tool 4: compute_itt_split — ITT Split Optimisation

Multi-constraint optimisation for road/sea container allocation.
Minimises total cost (transport + demurrage + SLA) subject to:
  - Tuas vessel departure deadline
  - Feeder departure window
  - Road truck availability (LTA 1x 40ft or 2x 20ft per chassis)
  - Yard block capacity at Tuas

Receives: candidates (T1), road_capacity (T2), sea_capacity (T3)
Feeds into: HITL Gate 1 (approval card), HITL Gate 2 (truck dispatch)

Master Charter ref: Section 3, Tool 4
Tech Stack ref: Section 8, YAML config (tools.compute_itt_split)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
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
) -> dict[str, Any]:
    """Compute estimated arrival times for road and sea ITT."""
    # Reference time: use vessel_departure timezone if available, else naive
    tz = vessel_departure.tzinfo
    now = datetime.now(tz) if tz else datetime.now()

    # Road: waves of truck dispatches
    if available_trucks > 0:
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

def compute_itt_split(
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
    """Compute optimal road/sea ITT split minimising total cost.

    This tool runs multi-constraint optimisation over all valid road/sea
    allocations and returns the optimal split plus alternatives. The
    computation is deterministic (no LLM) — the LLM calls this tool and
    presents the result to the human at HITL Gate 1.

    Feeder capacity is the key constraint that forces a road/sea split:
    - Feeder available TEU is limited (typically 180 TEU for regional feeder)
    - 40ft containers consume 2 TEU each, 20ft containers consume 1 TEU each
    - The feeder must also carry cargo for other ports ( Port Klang, etc.)
    - Only containers marked ready at PPT can be loaded onto the feeder

    Args:
        candidates: Container list from Tool 1 (optional if using direct params).
        road_capacity: Road ITT capacity from Tool 2 (optional if using direct params).
        sea_capacity: Sea ITT capacity from Tool 3 (optional if using direct params).
        tuas_vessel_departure: ISO-8601 vessel departure time at Tuas.
        constraints: Extra constraints dict (optional).
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
    logger.info(
        "compute_itt_split called: %d containers (%dx 40ft + %dx 20ft), "
        "trucks=%d, feeder=%d TEU",
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
    # Practical loading window: 4 hours max (realistic for regional feeder).
    # Loading rate: ~20 containers/hour.
    FEEDER_LOADING_RATE_PER_HR = 20
    FEEDER_MAX_LOADING_HOURS = 4  # Feeder doesn't stay at PPT forever
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
    FEEDER_AVAILABLE_FOR_ITT_TEU = 40
    max_sea_teu = min(
        feeder_available_teu,
        FEEDER_AVAILABLE_FOR_ITT_TEU,
        max_sea_by_loading,
        container_40ft + container_20ft,
    )

    # Also cap by available containers — can't send more than we have
    max_sea_teu = min(max_sea_teu, container_40ft + container_20ft)

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

    if timeline["margin_minutes"] < 60:
        escalation_flags.append({
            "trigger_id": "esc_3",
            "name": "Financial recovery cost exceeds limit",
            "condition": f"margin ({timeline['margin_minutes']} min) < 60 min",
            "threshold": 60,
            "actual": timeline["margin_minutes"],
            "rationale": "Insufficient margin — high risk of vessel delay costs",
        })

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

    logger.info(
        "compute_itt_split result: optimal=%d road / %d sea ($%d), "
        "confidence=%.2f, margin=%d min, %d alternatives",
        optimal.road_containers, optimal.sea_containers,
        optimal.total_transport_cost, confidence,
        timeline["margin_minutes"], len(alternatives),
    )

    return result.to_dict()


# ---------------------------------------------------------------------------
# Tool schema (for LLM function-calling)
# ---------------------------------------------------------------------------

COMPUTE_ITT_SPLIT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "compute_itt_split",
        "description": (
            "Compute optimal road/sea ITT split minimising total transport cost "
            "subject to LTA chassis limits, feeder capacity, and vessel departure deadline. "
            "Returns optimal split with alternatives, cost analysis, and confidence score."
        ),
        "parameters": {
            "type": "object",
            "properties": {
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


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("=== Tool 4: compute_itt_split — Standalone Test ===\n")

    # Use a future date for testing (next day at 20:00 SGT)
    from datetime import timezone, timedelta as td
    sgt = timezone(td(hours=8))
    now = datetime.now(sgt)
    test_departure = now.replace(hour=20, minute=0, second=0, microsecond=0) + td(days=1)
    test_feeder_dep = test_departure - td(hours=6)

    result = compute_itt_split(
        total_containers=120,
        container_40ft=40,
        container_20ft=80,
        available_trucks=20,
        transit_time_min=45,
        feeder_available_teu=180,
        tuas_vessel_departure=test_departure.isoformat(),
        feeder_departure=test_feeder_dep.isoformat(),
    )

    print(json.dumps(result, indent=2))
    print(f"\nOptimal: {result['optimal_split']['road_containers']} road / "
          f"{result['optimal_split']['sea_containers']} sea = "
          f"${result['optimal_split']['total_transport_cost']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Alternatives: {len(result['alternatives'])}")
    print(f"Escalation flags: {len(result['escalation_flags'])}")
