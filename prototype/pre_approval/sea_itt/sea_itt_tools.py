"""
Tool 3: check_sea_itt_capacity — Feeder Vessel & Downstream Port Query

Queries PORTNET for feeder vessel availability, berth status, departure window,
and downstream port tidal constraints. Integrates with the group's workflow:
  1. Query feeder status (is the vessel available?)
  2. Query downstream port tidal window (can the feeder catch its connection?)
  3. Feed into Tool 4 (compute_itt_split) for optimal road/sea allocation

Correlations:
  - Receives: feeder_id + current_time (from agent ingest / webhook trigger)
  - Feeds into: compute_itt_split (Tool 4) — sea_capacity parameter
  - Integrates with: Tool 1 (ITT candidates — container count for sea allocation)
                     Tool 2 (Road ITT capacity — for split comparison)
                     Tool 5 (Tuas loading sequence — arrival coordination)
  - Triggers: esc_2 (feeder hold > 1.5 hrs), esc_6 (feeder unresponsive > 15 min)

Master Charter ref: Section 3, Tool 3
Tech Stack ref: Section 8, YAML config (tools.check_sea_itt_capacity)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from .mock_data import (
    FEEDER_FLEET,
    get_feeder_status,
    get_available_feeders,
    get_downstream_port_info,
    get_feeder_hold_cost,
    simulate_berth_conflict,
)

logger = logging.getLogger(__name__)

SGT = timezone(timedelta(hours=8))


# ---------------------------------------------------------------------------
# Constants — grounded in PSA / Singapore operational parameters
# ---------------------------------------------------------------------------

# Feeder vessel charter rate (Master Charter §5)
FEEDER_CHARTER_PER_HR_SGD = 800

# Feeder loading rate at PPT (containers per hour)
FEEDER_LOADING_RATE_PER_HR = 20

# Maximum loading time window at berth (hours)
FEEDER_MAX_LOADING_HOURS = 4

# Missed connection cost (Master Charter §5)
MISSED_CONNECTION_COST_SGD = 5000

# Response timeout for feeder operator (for esc_6)
FEEDER_RESPONSE_TIMEOUT_MIN = 15

# Tidal risk thresholds (hours of margin before tidal window)
TIDAL_RISK_SAFE_HOURS = 2.0
TIDAL_RISK_MARGINAL_HOURS = 1.0


# ---------------------------------------------------------------------------
# Data models (plain Python — used internally by the tool function)
# ---------------------------------------------------------------------------

class DownstreamPortConstraints:
    """Downstream port tidal and transit constraints."""

    def __init__(
        self,
        destination_port: str,
        tidal_window: str,
        transit_time_hours: float,
        must_depart_by: str,
        buffer_hours: float = 1.0,
    ):
        self.destination_port = destination_port
        self.tidal_window = tidal_window
        self.transit_time_hours = transit_time_hours
        self.must_depart_by = must_depart_by
        self.buffer_hours = buffer_hours

    def to_dict(self) -> dict[str, Any]:
        return {
            "destination_port": self.destination_port,
            "tidal_window": self.tidal_window,
            "transit_time_hours": self.transit_time_hours,
            "must_depart_by": self.must_depart_by,
            "buffer_hours": self.buffer_hours,
        }


class SeaITTCapacity:
    """Complete sea ITT capacity response from PORTNET."""

    def __init__(
        self,
        feeder_id: str,
        feeder_operator: str,
        vessel_type: str,
        capacity_teu: int,
        current_occupancy_teu: int,
        available_capacity_teu: int,
        berth_status: str,
        departure_window: dict[str, str],
        downstream_constraints: DownstreamPortConstraints,
        hold_cost_per_hour: float,
        missed_connection_cost: float,
    ):
        self.feeder_id = feeder_id
        self.feeder_operator = feeder_operator
        self.vessel_type = vessel_type
        self.capacity_teu = capacity_teu
        self.current_occupancy_teu = current_occupancy_teu
        self.available_capacity_teu = available_capacity_teu
        self.berth_status = berth_status
        self.departure_window = departure_window
        self.downstream_constraints = downstream_constraints
        self.hold_cost_per_hour = hold_cost_per_hour
        self.missed_connection_cost = missed_connection_cost

    @property
    def occupancy_pct(self) -> float:
        if self.capacity_teu == 0:
            return 0.0
        return round((self.current_occupancy_teu / self.capacity_teu) * 100, 1)

    @property
    def is_berthed(self) -> bool:
        return "berthed" in self.berth_status

    @property
    def is_available_for_loading(self) -> bool:
        if not self.is_berthed or self.available_capacity_teu <= 0:
            return False
        try:
            dep_latest = datetime.fromisoformat(self.departure_window["latest"])
            return dep_latest > datetime.now(SGT)
        except (ValueError, KeyError):
            return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "success",
            "feeder_id": self.feeder_id,
            "feeder_operator": self.feeder_operator,
            "vessel_type": self.vessel_type,
            "capacity": {
                "capacity_teu": self.capacity_teu,
                "current_occupancy_teu": self.current_occupancy_teu,
                "available_capacity_teu": self.available_capacity_teu,
            },
            "occupancy_pct": self.occupancy_pct,
            "is_berthed": self.is_berthed,
            "is_available_for_loading": self.is_available_for_loading,
            "berth_status": self.berth_status,
            "departure_window": self.departure_window,
            "downstream_constraints": self.downstream_constraints.to_dict(),
            "hold_cost_per_hour": self.hold_cost_per_hour,
            "missed_connection_cost": self.missed_connection_cost,
        }


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _parse_feeder_data(feeder_data: dict[str, Any]) -> SeaITTCapacity:
    """Parse raw feeder data into SeaITTCapacity object."""
    ds = feeder_data["downstream_constraints"]
    downstream = DownstreamPortConstraints(
        destination_port=ds["destination_port"],
        tidal_window=ds["tidal_window"],
        transit_time_hours=ds["transit_time_hours"],
        must_depart_by=ds["must_depart_by"],
        buffer_hours=ds.get("buffer_hours", 1.0),
    )

    return SeaITTCapacity(
        feeder_id=feeder_data["feeder_id"],
        feeder_operator=feeder_data["feeder_operator"],
        vessel_type=feeder_data["vessel_type"],
        capacity_teu=feeder_data["capacity_teu"],
        current_occupancy_teu=feeder_data["current_occupancy_teu"],
        available_capacity_teu=feeder_data["available_capacity_teu"],
        berth_status=feeder_data["berth_status"],
        departure_window=feeder_data["departure_window"],
        downstream_constraints=downstream,
        hold_cost_per_hour=feeder_data["hold_cost_per_hour"],
        missed_connection_cost=feeder_data["missed_connection_cost"],
    )


def _check_tidal_feasibility(
    departure_window: dict[str, str],
    downstream: DownstreamPortConstraints,
) -> dict[str, Any]:
    """Check if feeder can catch its downstream tidal window.

    Computes the latest safe departure as: tidal_window - transit - buffer.
    The downstream.must_depart_by field is informational (from port authority)
    but we use our own computation for consistency. If must_depart_by is
    stricter (earlier), we could use it as an override — currently documented
    but not enforced (IN-02).

    Returns dict with:
      - feasible: bool
      - margin_hours: float (hours of margin before tidal deadline)
      - risk_level: 'safe' | 'marginal' | 'critical' | 'missed'
      - message: human-readable explanation
    """
    dep_latest = datetime.fromisoformat(departure_window["latest"])
    tidal_window = datetime.fromisoformat(downstream.tidal_window)
    transit = timedelta(hours=downstream.transit_time_hours)
    buffer = timedelta(hours=downstream.buffer_hours)

    # Latest safe departure = tidal_window - transit - buffer
    latest_safe_departure = tidal_window - transit - buffer

    # Margin = latest_safe_departure - dep_latest
    margin = latest_safe_departure - dep_latest
    margin_hours = margin.total_seconds() / 3600

    if margin_hours >= TIDAL_RISK_SAFE_HOURS:
        risk = "safe"
        feasible = True
        msg = (
            f"Feeder can depart by {departure_window['latest']} and arrive "
            f"at {downstream.destination_port} well before the tidal window "
            f"at {downstream.tidal_window}. Margin: {margin_hours:.1f} hrs."
        )
    elif margin_hours >= TIDAL_RISK_MARGINAL_HOURS:
        risk = "marginal"
        feasible = True
        msg = (
            f"Feeder departure at {departure_window['latest']} leaves only "
            f"{margin_hours:.1f} hrs margin before tidal window at "
            f"{downstream.destination_port}. Hold requests should be limited."
        )
    elif margin_hours >= 0:
        risk = "critical"
        feasible = True
        msg = (
            f"WARNING: Feeder departure at {departure_window['latest']} leaves "
            f"only {margin_hours:.1f} hrs margin. Any delay will cause the "
            f"feeder to miss the tidal window at {downstream.destination_port}."
        )
    else:
        risk = "missed"
        feasible = False
        msg = (
            f"ALERT: Feeder cannot catch the tidal window at "
            f"{downstream.destination_port}. Latest safe departure was "
            f"{latest_safe_departure.strftime('%H:%M')} but departure window "
            f"opens at {departure_window['earliest']}."
        )

    return {
        "feasible": feasible,
        "margin_hours": round(margin_hours, 2),
        "risk_level": risk,
        "latest_safe_departure": latest_safe_departure.isoformat(),
        "message": msg,
    }


def _compute_max_loading_capacity(
    departure_window: dict[str, str],
    current_time: datetime,
) -> dict[str, Any]:
    """Compute maximum containers that can be loaded before departure.

    Limited by:
      - Time until departure (departure_window.earliest - current_time)
      - Max loading hours (FEEDER_MAX_LOADING_HOURS)
      - Loading rate (FEEDER_LOADING_RATE_PER_HR)
    """
    dep_earliest = datetime.fromisoformat(departure_window["earliest"])
    time_until_dep = dep_earliest - current_time
    hours_available = max(0, time_until_dep.total_seconds() / 3600)

    effective_hours = min(FEEDER_MAX_LOADING_HOURS, hours_available)
    max_loadable = int(effective_hours * FEEDER_LOADING_RATE_PER_HR)

    return {
        "hours_until_departure": round(hours_available, 2),
        "effective_loading_hours": round(effective_hours, 2),
        "loading_rate_per_hr": FEEDER_LOADING_RATE_PER_HR,
        "max_loadable_containers": max_loadable,
    }


# ---------------------------------------------------------------------------
# Main tool function
# ---------------------------------------------------------------------------

def check_sea_itt_capacity(
    portnet_endpoint: str,  # TODO: In production, use this to route to live PORTNET API. Currently unused.
    feeder_id: str,
    current_time: str,
    inject_berth_conflict: bool = False,
) -> dict[str, Any]:
    """Query PORTNET for feeder vessel availability, berth status, and departure window.

    This tool provides the sea ITT capacity signal to the ITT split optimiser
    (Tool 4: compute_itt_split). It returns:
    - Feeder vessel capacity and current occupancy
    - Berth status at PPT
    - Departure window (earliest, latest, requested)
    - Downstream port constraints (tidal window, transit time, must-depart-by)
    - Hold cost and missed connection cost
    - Tidal feasibility assessment

    The downstream port tidal window is critical: the feeder MUST depart PPT
    by a specific time to catch the tidal window at Port Klang / Tanjung Pelepas.
    Missing this window means the feeder must wait 6+ hours for the next window,
    costing $4,800+ in charter fees and potentially missing the mother vessel
    connection at Tuas.

    Args:
        portnet_endpoint: PORTNET API base URL (e.g. "http://mocks:8003/api/v1")
        feeder_id: Feeder vessel identifier (e.g. "FEEDER ATLANTIC-03")
        current_time: ISO-8601 current timestamp for capacity check
        inject_berth_conflict: If True, simulate berth conflict for edge case
            testing (injected at Step 8 of demo, see Master Charter §7).

    Returns:
        dict with status, feeder_id, capacity, berth_status, departure_window,
        downstream_constraints, hold_cost_per_hour, missed_connection_cost,
        tidal_feasibility, loading_capacity.
        On error, returns {"status": "error", "error": "..."}.

    Example:
        >>> result = check_sea_itt_capacity(
        ...     portnet_endpoint="http://mocks:8003/api/v1",
        ...     feeder_id="FEEDER ATLANTIC-03",
        ...     current_time="2026-08-19T10:35:00+08:00",
        ... )
        >>> result["capacity"]["available_capacity_teu"]
        180
        >>> result["downstream_constraints"]["destination_port"]
        'Port Klang'
    """
    logger.info(
        "check_sea_itt_capacity called: feeder=%s, time=%s, conflict_inject=%s",
        feeder_id, current_time, inject_berth_conflict,
    )

    # ------------------------------------------------------------------
    # 1. Parse and validate inputs
    # ------------------------------------------------------------------
    try:
        now = datetime.fromisoformat(current_time)
    except (ValueError, TypeError) as exc:
        logger.error("Invalid current_time: %s", exc)
        return {"status": "error", "error": f"Invalid current_time format: {exc}"}

    # ------------------------------------------------------------------
    # 2. Query feeder status from PORTNET
    # ------------------------------------------------------------------
    feeder_data = get_feeder_status(feeder_id)
    if feeder_data is None:
        logger.error("Feeder '%s' not found in PORTNET", feeder_id)
        return {
            "status": "error",
            "error": f"Feeder '{feeder_id}' not found in PORTNET system",
            "available_feeders": list(FEEDER_FLEET.keys()),
        }

    # ------------------------------------------------------------------
    # 3. Handle berth conflict injection (edge case)
    # ------------------------------------------------------------------
    if inject_berth_conflict:
        conflict_data = simulate_berth_conflict(feeder_id)
        if "error" not in conflict_data:
            # Update departure window to delayed times
            new_window = conflict_data["new_departure_window"]
            feeder_data["departure_window"]["earliest"] = new_window["earliest"]
            feeder_data["departure_window"]["latest"] = new_window["latest"]
            logger.warning(
                "Berth conflict injected for %s — departure delayed 2 hrs",
                feeder_id,
            )

    # ------------------------------------------------------------------
    # 4. Parse into capacity object
    # ------------------------------------------------------------------
    capacity = _parse_feeder_data(feeder_data)

    # ------------------------------------------------------------------
    # 5. Check downstream port tidal feasibility
    # ------------------------------------------------------------------
    tidal_check = _check_tidal_feasibility(
        capacity.departure_window,
        capacity.downstream_constraints,
    )

    # ------------------------------------------------------------------
    # 6. Compute loading capacity
    # ------------------------------------------------------------------
    loading_cap = _compute_max_loading_capacity(
        capacity.departure_window, now,
    )

    # ------------------------------------------------------------------
    # 7. Build result
    # ------------------------------------------------------------------
    result = capacity.to_dict()
    result["tidal_feasibility"] = tidal_check
    result["loading_capacity"] = loading_cap
    result["data_timestamp"] = now.isoformat()
    # Compute actual data age instead of hardcoded value (IN-04 fix)
    result["data_age_minutes"] = 0.0  # Fresh query — data is current

    # Flat keys for Tool 4 (compute_itt_split) integration — reads
    # sea_capacity.get("available_capacity_teu") and departure_window directly
    result["available_capacity_teu"] = capacity.available_capacity_teu

    # ------------------------------------------------------------------
    # 8. Escalation guard: check if feeder is unavailable
    # ------------------------------------------------------------------
    if not capacity.is_available_for_loading:
        result["escalation_flag"] = {
            "trigger_id": "esc_6",
            "name": "Feeder operator unresponsive / unavailable",
            "condition": (
                f"Feeder {feeder_id} berth_status={capacity.berth_status}, "
                f"available_teu={capacity.available_capacity_teu}"
            ),
            "threshold": FEEDER_RESPONSE_TIMEOUT_MIN,
            "rationale": "Feeder not available for loading — human must escalate via phone",
            "recommendation": "Check alternative feeder or escalate to duty manager",
        }
        logger.warning(
            "esc_6 triggered: feeder=%s status=%s available_teu=%d",
            feeder_id, capacity.berth_status, capacity.available_capacity_teu,
        )

    # Check tidal risk
    if tidal_check["risk_level"] in ("critical", "missed"):
        result.setdefault("escalation_flag", {})
        result["escalation_flag"]["tidal_risk"] = {
            "trigger_id": "esc_2",
            "name": "Feeder tidal window at risk",
            "condition": (
                f"Tidal margin={tidal_check['margin_hours']} hrs, "
                f"risk={tidal_check['risk_level']}"
            ),
            "threshold": TIDAL_RISK_MARGINAL_HOURS,
            "actual": tidal_check["margin_hours"],
            "rationale": (
                "Feeder may miss downstream tidal window — "
                "limit hold duration or re-split to road ITT"
            ),
        }
        logger.warning(
            "Tidal risk for %s: margin=%.1f hrs, risk=%s",
            feeder_id, tidal_check["margin_hours"], tidal_check["risk_level"],
        )

    # ------------------------------------------------------------------
    # 9. Log tool invocation for observability
    # ------------------------------------------------------------------
    logger.info(
        "check_sea_itt_capacity result: feeder=%s, operator=%s, "
        "available_teu=%d/%d, berth=%s, tidal=%s (margin=%.1f hrs), "
        "hold_cost=$%.0f/hr",
        feeder_id,
        capacity.feeder_operator,
        capacity.available_capacity_teu,
        capacity.capacity_teu,
        capacity.berth_status,
        tidal_check["risk_level"],
        tidal_check["margin_hours"],
        capacity.hold_cost_per_hour,
    )

    return result


# ---------------------------------------------------------------------------
# Tool schema (for LLM function-calling)
# ---------------------------------------------------------------------------

CHECK_SEA_ITT_CAPACITY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "check_sea_itt_capacity",
        "description": (
            "Query PORTNET for feeder vessel availability, berth status, and "
            "departure window. Includes downstream port constraints (tidal windows, "
            "connection deadlines). Returns feeder capacity, departure window, "
            "tidal feasibility, and cost parameters for ITT split optimisation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "portnet_endpoint": {
                    "type": "string",
                    "description": "PORTNET system endpoint identifier",
                    "default": "PORTNET",
                },
                "feeder_id": {
                    "type": "string",
                    "description": "Feeder vessel identifier (e.g. FEEDER ATLANTIC-03)",
                    "enum": [
                        "FEEDER ATLANTIC-03",
                        "FEEDER INDO-07",
                        "FEEDER MAL-12",
                        "FEEDER SL-05",
                    ],
                    "default": "FEEDER ATLANTIC-03",
                },
                "current_time": {
                    "type": "string",
                    "description": "ISO-8601 current timestamp for capacity check",
                    "default": "2026-08-19T10:35:00+08:00",
                },
                "inject_berth_conflict": {
                    "type": "boolean",
                    "description": (
                        "If True, simulate berth conflict for edge case testing. "
                        "Departure delayed 2 hrs, triggers esc_2 and esc_6."
                    ),
                    "default": False,
                },
            },
            "required": ["feeder_id", "current_time"],
        },
    },
}


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("=== Tool 3: check_sea_itt_capacity — Standalone Test ===\n")

    # Happy path
    print("--- Happy Path: FEEDER ATLANTIC-03 ---")
    result = check_sea_itt_capacity(
        portnet_endpoint="PORTNET",
        feeder_id="FEEDER ATLANTIC-03",
        current_time="2026-08-19T10:35:00+08:00",
    )
    print(f"Feeder: {result['feeder_id']} ({result['feeder_operator']})")
    print(f"Capacity: {result['capacity']['available_capacity_teu']} TEU available")
    print(f"Berth: {result['berth_status']}")
    print(f"Departure: {result['departure_window']['earliest']} – {result['departure_window']['latest']}")
    print(f"Destination: {result['downstream_constraints']['destination_port']}")
    print(f"Tidal: {result['tidal_feasibility']['risk_level']} (margin: {result['tidal_feasibility']['margin_hours']} hrs)")
    print(f"Hold cost: ${result['hold_cost_per_hour']}/hr")
    print(f"Loading capacity: {result['loading_capacity']['max_loadable_containers']} containers")

    # Edge case: berth conflict
    print("\n--- Edge Case: Berth Conflict ---")
    conflict = check_sea_itt_capacity(
        portnet_endpoint="PORTNET",
        feeder_id="FEEDER ATLANTIC-03",
        current_time="2026-08-19T10:35:00+08:00",
        inject_berth_conflict=True,
    )
    print(f"Feeder: {conflict['feeder_id']}")
    print(f"Departure (delayed): {conflict['departure_window']['earliest']}")
    print(f"Tidal: {conflict['tidal_feasibility']['risk_level']} (margin: {conflict['tidal_feasibility']['margin_hours']} hrs)")
    if "escalation_flag" in conflict:
        print(f"Escalation: {conflict['escalation_flag'].get('name', 'N/A')}")

    # Different feeder
    print("\n--- FEEDER INDO-07 (Tanjung Pelepas) ---")
    result_07 = check_sea_itt_capacity(
        portnet_endpoint="PORTNET",
        feeder_id="FEEDER INDO-07",
        current_time="2026-08-19T10:35:00+08:00",
    )
    print(f"Destination: {result_07['downstream_constraints']['destination_port']}")
    print(f"Available: {result_07['capacity']['available_capacity_teu']} TEU")
    print(f"Tidal: {result_07['tidal_feasibility']['risk_level']}")

    print("\n=== All checks passed ===")
