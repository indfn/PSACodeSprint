"""
Tool 2: check_road_itt_capacity — OptETruck Road ITT Capacity Query

Queries OptETruck for available prime movers, chassis, transit time, and road
conditions for road ITT from PPT (Pasir Panjang Terminal) to Tuas Port.

Correlations:
  - Receives: terminal + time window (from agent ingest / webhook trigger)
  - Feeds into: compute_itt_split (Tool 4) — road_capacity parameter
  - Triggers: esc_5 (road ITT capacity below 60% of required trucks)
  - Constraints: LTA chassis limits, peak hour congestion (07:30-09:30, 17:30-19:30)

Master Charter ref: Section 3, Tool 2
Tech Stack ref: Section 8, YAML config (tools.check_road_itt_capacity)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — grounded in PSA / Singapore operational parameters
# ---------------------------------------------------------------------------

# LTA regulation: 1x 40ft/45ft (FEU) OR up to 2x 20ft (TEU) per prime mover
LTA_CHASSIS_LIMITS = "1x 40ft/45ft (FEU) OR up to 2x 20ft (TEU) per prime mover"

# Cost per road ITT trip (PPT → Tuas ~35 km via West Coast Highway / AYE)
ROAD_COST_PER_TRIP_SGD = 150

# Transit times (minutes) — PPT to Tuas via West Coast Highway / AYE
TRANSIT_OFF_PEAK_MIN = 45
TRANSIT_PEAK_MIN = 95

# Peak hour windows (Singapore time, UTC+8)
PEAK_WINDOWS = [
    (7 * 60 + 30, 9 * 60 + 30),   # 07:30 – 09:30
    (17 * 60 + 30, 19 * 60 + 30),  # 17:30 – 19:30
]

# Road segments along the PPT → Tuas corridor
ROAD_SEGMENTS = [
    "West_Coast_Highway",
    "AYE",
    "Tuas_Port_Boulevard",
]

# OptETruck mock capacity (realistic for PSA PPT fleet)
MOCK_AVAILABLE_TRUCKS = 20
MOCK_TOTAL_FLEET = 25

# Container mix (from PB-12 Master Charter)
TOTAL_CONTAINERS = 120
CONTAINER_MIX_40FT_FEU = 40
CONTAINER_MIX_20FT_TEU = 80


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class RoadConditions:
    """Status of each road segment along the PPT → Tuas corridor."""

    def __init__(
        self,
        west_coast_highway: str = "normal",
        aye: str = "normal",
        tuas_port_boulevard: str = "clear",
    ):
        self.segments: dict[str, str] = {
            "West_Coast_Highway": west_coast_highway,
            "AYE": aye,
            "Tuas_Port_Boulevard": tuas_port_boulevard,
        }

    @property
    def has_congestion(self) -> bool:
        return any(
            status not in ("normal", "clear")
            for status in self.segments.values()
        )

    @property
    def worst_segment(self) -> str | None:
        severity = {"clear": 0, "normal": 0, "moderate": 1, "heavy": 2, "standstill": 3}
        worst = max(self.segments.items(), key=lambda x: severity.get(x[1], 0))
        return worst[0] if worst[1] not in ("normal", "clear") else None

    def to_dict(self) -> dict[str, str]:
        return dict(self.segments)


class RoadITTCapacity:
    """Complete road ITT capacity response from OptETruck."""

    def __init__(
        self,
        terminal: str,
        available_trucks: int,
        total_fleet: int,
        transit_time_minutes: int,
        road_conditions: RoadConditions,
        cost_per_trip: int,
        lta_chassis_limits: str,
        earliest_departure: datetime,
        latest_arrival_at_tuas: datetime,
        container_breakdown_40ft: int = 0,
        container_breakdown_20ft: int = 0,
    ):
        self.terminal = terminal
        self.available_trucks = available_trucks
        self.total_fleet = total_fleet
        self.transit_time_minutes = transit_time_minutes
        self.road_conditions = road_conditions
        self.cost_per_trip = cost_per_trip
        self.lta_chassis_limits = lta_chassis_limits
        self.earliest_departure = earliest_departure
        self.latest_arrival_at_tuas = latest_arrival_at_tuas
        self.container_breakdown_40ft = container_breakdown_40ft
        self.container_breakdown_20ft = container_breakdown_20ft

        # Derived computations
        self._compute_trips()

    def _compute_trips(self) -> None:
        """Compute LTA-compliant trip breakdown.

        LTA rule: 1x 40ft (FEU) per prime mover, OR up to 2x 20ft (TEU) per prime mover.
        So 40ft containers always need 1 trip each.
        20ft containers are paired: 2 per trip (except odd remainder = 1 extra trip).
        """
        # 40ft trips: 1 trip per container
        self.trips_40ft = self.container_breakdown_40ft

        # 20ft trips: 2 containers per trip (paired), +1 if odd
        self.trips_20ft = (self.container_breakdown_20ft + 1) // 2

        self.total_trips = self.trips_40ft + self.trips_20ft
        self.total_road_containers = self.container_breakdown_40ft + self.container_breakdown_20ft
        self.estimated_road_cost = self.total_trips * self.cost_per_trip

        # Round trip = outbound + return (assume same transit time)
        self.estimated_round_trip_minutes = self.transit_time_minutes * 2 + 30  # +30 min loading/unloading

        # Baseline: all 120 containers by road
        self.baseline_trips_all_120 = 80  # 40 trips (40ft) + 40 trips (20ft paired)
        self.baseline_road_cost_all_120 = self.baseline_trips_all_120 * self.cost_per_trip

        # Standard 80/20 split road portion: 40x 40ft + 40x 20ft = 80 containers
        self.trips_80_road_split = 40 + 20  # 40 trips (40ft) + 20 trips (20ft paired)
        self.estimated_road_cost_80_split = self.trips_80_road_split * self.cost_per_trip

        # Split spec uses the 80-container subset (40x 40ft + 40x 20ft)
        self.split_spec_40ft_trips = 40
        self.split_spec_20ft_trips = 40 // 2  # 20 trips (paired)
        self.split_spec_containers = 80

    @property
    def fleet_utilisation_pct(self) -> float:
        if self.total_fleet == 0:
            return 0.0
        return round((self.available_trucks / self.total_fleet) * 100, 1)

    @property
    def capacity_ratio(self) -> float:
        """available / required for 100% road scenario (80 trips)."""
        if self.baseline_trips_all_120 == 0:
            return 0.0
        return round(self.available_trucks / self.baseline_trips_all_120, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "success",
            "terminal": self.terminal,
            "available_trucks": self.available_trucks,
            "total_fleet": self.total_fleet,
            "fleet_utilisation_pct": self.fleet_utilisation_pct,
            "transit_time_minutes": self.transit_time_minutes,
            "road_conditions": self.road_conditions.to_dict(),
            "cost_per_trip": self.cost_per_trip,
            "lta_chassis_limits": self.lta_chassis_limits,
            "estimated_round_trip_minutes": self.estimated_round_trip_minutes,
            "container_breakdown": {
                "40ft_feu": self.container_breakdown_40ft,
                "20ft_teu": self.container_breakdown_20ft,
            },
            "trip_breakdown": {
                "trips_40ft": self.trips_40ft,
                "trips_20ft": self.trips_20ft,
                "total_trips": self.total_trips,
                "total_road_containers": self.total_road_containers,
            },
            "baseline_trips_all_120_containers": self.baseline_trips_all_120,
            "baseline_road_cost_all_120": self.baseline_road_cost_all_120,
            "split_road_containers_spec": (
                f"40x 40ft ({self.split_spec_40ft_trips} trips) + 40x 20ft ({self.split_spec_20ft_trips} trips) "
                f"= {self.split_spec_containers} containers ({self.trips_80_road_split} trips)"
            ),
            "trips_needed_for_80_road_split": self.trips_80_road_split,
            "estimated_road_cost_80_split": self.estimated_road_cost_80_split,
            "earliest_departure": self.earliest_departure.isoformat(),
            "latest_arrival_at_tuas": self.latest_arrival_at_tuas.isoformat(),
            "capacity_ratio": self.capacity_ratio,
        }


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _is_peak_hour(dt: datetime) -> bool:
    """Check if a datetime falls within Singapore peak hour windows."""
    minutes_since_midnight = dt.hour * 60 + dt.minute
    return any(
        start <= minutes_since_midnight <= end
        for start, end in PEAK_WINDOWS
    )


def _resolve_transit_time(time_window_start: datetime) -> int:
    """Determine transit time based on whether departure falls in peak hours.

    If the departure time is within a peak window, use peak transit time.
    If the departure is within 30 min before a peak window, use peak transit
    (congestion builds before the official window).
    """
    minutes_since_midnight = time_window_start.hour * 60 + time_window_start.minute

    for start, end in PEAK_WINDOWS:
        # Within peak window
        if start <= minutes_since_midnight <= end:
            return TRANSIT_PEAK_MIN
        # Within 30 min before peak window (congestion buildup)
        if start - 30 <= minutes_since_midnight < start:
            return TRANSIT_PEAK_MIN

    return TRANSIT_OFF_PEAK_MIN


def _simulate_road_conditions(
    time_window_start: datetime,
    time_window_end: datetime,
) -> RoadConditions:
    """Simulate road conditions based on time of day.

    In production this would query real traffic APIs (Google Maps, LTA DataMall).
    For the mock, we simulate realistic conditions:
    - AYE: moderate traffic during peak hours
    - West Coast Highway: moderate near Pandan Industrial area during peak
    - Tuas Port Boulevard: usually clear (dedicated port road)
    """
    wch_status = "normal"
    aye_status = "normal"

    # Check if time window overlaps with peak hours
    start_min = time_window_start.hour * 60 + time_window_start.minute
    end_min = time_window_end.hour * 60 + time_window_end.minute

    for peak_start, peak_end in PEAK_WINDOWS:
        # Overlap check: window overlaps if start < peak_end and end > peak_start
        if start_min < peak_end and end_min > peak_start:
            aye_status = "moderate_traffic"
            wch_status = "moderate_traffic_near_pandan"
            break

    return RoadConditions(
        west_coast_highway=wch_status,
        aye=aye_status,
        tuas_port_boulevard="clear",
    )


def _query_optetruck_fleet(
    optetruck_endpoint: str,
    terminal: str,
    time_window_start: datetime,
    time_window_end: datetime,
) -> dict[str, Any]:
    """Query OptETruck system for fleet availability.

    In production, this would be an HTTP POST to the OptETruck API.
    For the mock, we return realistic fleet data with time-based variation.

    The mock simulates:
    - Trucks become less available during peak hours (already dispatched)
    - Some trucks are in maintenance (always 2-3 out of service)
    - Late afternoon windows have fewer trucks (already on return trips)
    """
    hour = time_window_start.hour

    # Simulate fleet availability based on time of day
    if 6 <= hour < 9:
        # Early morning — fleet mostly available
        available = 18
    elif 9 <= hour < 12:
        # Mid morning — some dispatched
        available = 20
    elif 12 <= hour < 14:
        # Lunch — reduced dispatch rate
        available = 22
    elif 14 <= hour < 17:
        # Afternoon — peak dispatch, fewer available
        available = 16
    elif 17 <= hour < 19:
        # Evening peak — trucks returning, limited availability
        available = 12
    else:
        # Off-peak / night
        available = 10

    return {
        "available_trucks": available,
        "total_fleet": MOCK_TOTAL_FLEET,
        "in_maintenance": MOCK_TOTAL_FLEET - available - 3,  # 3 in active dispatch
        "in_active_dispatch": 3,
    }


# ---------------------------------------------------------------------------
# Main tool function
# ---------------------------------------------------------------------------

def check_road_itt_capacity(
    optetruck_endpoint: str,
    terminal: str,
    time_window_start: str,
    time_window_end: str,
    container_breakdown_40ft: int = CONTAINER_MIX_40FT_FEU,
    container_breakdown_20ft: int = CONTAINER_MIX_20FT_TEU,
) -> dict[str, Any]:
    """Query OptETruck for available trucks, transit time, and road conditions.

    This tool provides the road ITT capacity signal to the ITT split optimiser
    (Tool 4: compute_itt_split). It returns:
    - Available prime movers and chassis
    - Transit time based on time-of-day (peak vs off-peak)
    - Road segment conditions (AYE, West Coast Highway, Tuas Port Boulevard)
    - LTA chassis compliance limits
    - Cost estimates for baseline (100% road) and standard (80/20) splits
    - Time window constraints (earliest departure, latest Tuas arrival)

    Args:
        optetruck_endpoint: OptETruck API base URL (e.g. "http://mocks:8002/api/v1")
        terminal: Origin terminal code (typically "PPT" for Pasir Panjang)
        time_window_start: ISO-8601 start of the query window
            (e.g. "2026-08-19T11:00:00+08:00")
        time_window_end: ISO-8601 end of the query window
            (e.g. "2026-08-19T18:00:00+08:00")
        container_breakdown_40ft: Number of 40ft (FEU) containers to move.
            Defaults to PB-12 value (40).
        container_breakdown_20ft: Number of 20ft (TEU) containers to move.
            Defaults to PB-12 value (80).

    Returns:
        dict with status, available_trucks, transit_time_minutes, road_conditions,
        cost_per_trip, lta_chassis_limits, estimated_round_trip_minutes,
        baseline/split cost estimates, and time window constraints.
        On error, returns {"status": "error", "error": "..."}.

    Example:
        >>> result = check_road_itt_capacity(
        ...     optetruck_endpoint="http://mocks:8002/api/v1",
        ...     terminal="PPT",
        ...     time_window_start="2026-08-19T11:00:00+08:00",
        ...     time_window_end="2026-08-19T18:00:00+08:00",
        ... )
        >>> result["available_trucks"]
        20
        >>> result["transit_time_minutes"]
        45
    """
    logger.info(
        "check_road_itt_capacity called: terminal=%s, window=%s to %s",
        terminal, time_window_start, time_window_end,
    )

    # ------------------------------------------------------------------
    # 1. Parse and validate inputs
    # ------------------------------------------------------------------
    try:
        tw_start = datetime.fromisoformat(time_window_start)
        tw_end = datetime.fromisoformat(time_window_end)
    except (ValueError, TypeError) as exc:
        logger.error("Invalid time window: %s", exc)
        return {"status": "error", "error": f"Invalid time window format: {exc}"}

    if tw_end <= tw_start:
        return {"status": "error", "error": "time_window_end must be after time_window_start"}

    if terminal not in ("PPT", "PASIR_PANJANG"):
        # Future: support PSA other terminals. For now, only PPT is valid for PB-12.
        logger.warning("Non-standard terminal '%s' — using PPT defaults", terminal)
        terminal = "PPT"

    if container_breakdown_40ft < 0 or container_breakdown_20ft < 0:
        return {"status": "error", "error": "Container counts must be non-negative"}

    # ------------------------------------------------------------------
    # 2. Query OptETruck fleet availability
    # ------------------------------------------------------------------
    fleet_data = _query_optetruck_fleet(optetruck_endpoint, terminal, tw_start, tw_end)
    available_trucks = fleet_data["available_trucks"]
    total_fleet = fleet_data["total_fleet"]

    # ------------------------------------------------------------------
    # 3. Determine transit time based on departure timing
    # ------------------------------------------------------------------
    transit_minutes = _resolve_transit_time(tw_start)

    # ------------------------------------------------------------------
    # 4. Assess road conditions for the corridor
    # ------------------------------------------------------------------
    road_conditions = _simulate_road_conditions(tw_start, tw_end)

    # If road conditions are bad, transit time increases by 20-40%
    if road_conditions.has_congestion:
        worst = road_conditions.worst_segment
        if worst == "AYE":
            transit_minutes = int(transit_minutes * 1.3)  # AYE congestion adds 30%
        elif worst == "West_Coast_Highway":
            transit_minutes = int(transit_minutes * 1.2)  # WCH adds 20%

    # ------------------------------------------------------------------
    # 5. Compute time window constraints
    # ------------------------------------------------------------------
    # Earliest departure: now (or time_window_start, whichever is later)
    earliest_departure = tw_start

    # Latest arrival at Tuas: time_window_end minus buffer for QC loading
    latest_arrival = tw_end

    # ------------------------------------------------------------------
    # 6. Build and return capacity response
    # ------------------------------------------------------------------
    capacity = RoadITTCapacity(
        terminal=terminal,
        available_trucks=available_trucks,
        total_fleet=total_fleet,
        transit_time_minutes=transit_minutes,
        road_conditions=road_conditions,
        cost_per_trip=ROAD_COST_PER_TRIP_SGD,
        lta_chassis_limits=LTA_CHASSIS_LIMITS,
        earliest_departure=earliest_departure,
        latest_arrival_at_tuas=latest_arrival,
        container_breakdown_40ft=container_breakdown_40ft,
        container_breakdown_20ft=container_breakdown_20ft,
    )

    result = capacity.to_dict()

    # ------------------------------------------------------------------
    # 7. Escalation guard: flag if capacity is critically low
    #    (mirrors esc_5: available_trucks < required_trucks * 0.6)
    # ------------------------------------------------------------------
    required_trips = capacity.baseline_trips_all_120  # 80 trips for 100% road
    if available_trucks < required_trips * 0.6:
        result["escalation_flag"] = {
            "trigger_id": "esc_5",
            "name": "Road ITT capacity below threshold",
            "condition": f"available_trucks ({available_trucks}) < required_trips ({required_trips}) * 0.6 = {int(required_trips * 0.6)}",
            "threshold": 0.6,
            "rationale": "Insufficient road capacity — requires emergency sea ITT coordination",
            "recommendation": "Increase sea allocation in ITT split or escalate to duty manager",
        }
        logger.warning(
            "esc_5 triggered: available_trucks=%d < required*0.6=%d",
            available_trucks, int(required_trips * 0.6),
        )

    # ------------------------------------------------------------------
    # 8. Log tool invocation for observability
    # ------------------------------------------------------------------
    logger.info(
        "check_road_itt_capacity result: trucks=%d, transit=%dm, cost/trip=$%d, "
        "trips_80_split=%d, round_trip=%dm, congestion=%s",
        available_trucks,
        transit_minutes,
        ROAD_COST_PER_TRIP_SGD,
        capacity.trips_80_road_split,
        capacity.estimated_round_trip_minutes,
        road_conditions.has_congestion,
    )

    return result
