from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from app.mocks.data import TRUCK_DATA, get_truck_data
from app.tools.base import BaseTool, ToolResult


def _parse_dt(value: str) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        pass
    m = re.search(r"(\d{1,2}):(\d{2})", value)
    if m:
        try:
            return datetime(2026, 8, 19, int(m.group(1)), int(m.group(2)), tzinfo=timezone.utc)
        except Exception:
            return None
    return None


PEAK_WINDOWS = [(7 * 60 + 30, 9 * 60 + 30), (17 * 60 + 30, 19 * 60 + 30)]


def _is_peak(dt: datetime | None) -> bool:
    if dt is None:
        return False
    mins = dt.hour * 60 + dt.minute
    for start, end in PEAK_WINDOWS:
        if start - 30 <= mins <= end + 20:
            return True
    return False


def _fleet_for_hour(hour: int | None) -> int:
    if hour is None:
        return TRUCK_DATA["available_trucks"]
    if 6 <= hour < 9:
        return 18
    if 9 <= hour < 12:
        return 20
    if 12 <= hour < 15:
        return 22
    return 20


class RoadITTCapacityTool(BaseTool):
    name = "check_road_itt_capacity"
    description = "Query OptETruck for available trucks, transit time, and road conditions for PPT→Tuas"
    parameters_schema = {
        "type": "object",
        "properties": {
            "terminal": {"type": "string", "description": "Origin terminal code e.g. PPT"},
            "time_window_start": {"type": "string", "description": "ISO8601 start of query window"},
            "time_window_end": {"type": "string", "description": "ISO8601 end of query window"},
            "current_time": {"type": "string", "description": "Optional ISO8601 current time for peak detection"},
        },
        "required": ["terminal", "time_window_start", "time_window_end"],
    }
    fallback_tool = "cached_road_capacity"
    timeout_seconds = 10

    async def execute(self, terminal: str, time_window_start: str, time_window_end: str, **kwargs) -> ToolResult:
        current_time = kwargs.get("current_time")
        base = get_truck_data(terminal=terminal)

        dt_start = _parse_dt(time_window_start)
        dt_current = _parse_dt(current_time) if current_time else None
        dt_for_peak = dt_current if dt_current is not None else dt_start

        peak = _is_peak(dt_for_peak)

        hour = dt_start.hour if dt_start is not None else None
        available = _fleet_for_hour(hour)
        total_fleet = base.get("total_fleet", TRUCK_DATA["total_fleet"])

        if peak:
            transit_time = 110
            road_conditions = {
                "AYE": "heavily_congested",
                "West_Coast_Highway": "moderate_traffic_near_pandan",
                "Tuas_Port_Boulevard": "clear",
            }
            confidence = 0.7
        else:
            transit_time = 90
            road_conditions = {
                "AYE": "normal",
                "West_Coast_Highway": "moderate_traffic_near_pandan",
                "Tuas_Port_Boulevard": "clear",
            }
            confidence = 0.95

        baseline_trips = TRUCK_DATA.get("baseline_trips_all_120_containers", 80)
        baseline_cost = TRUCK_DATA.get("baseline_road_cost_all_120", 12000)
        cost_per_trip = TRUCK_DATA.get("cost_per_trip", 150)
        lta_limits = TRUCK_DATA.get("lta_chassis_limits", "1x 40ft/45ft (FEU) OR up to 2x 20ft (TEU) per prime mover")

        capacity_ratio = round(available / baseline_trips, 2) if baseline_trips else 0.0
        fleet_utilisation = round((available / total_fleet) * 100, 1) if total_fleet else 0.0

        required_trips = baseline_trips
        esc_flag = available < required_trips * 0.6

        earliest_departure = base.get("earliest_departure", time_window_start)
        latest_arrival = base.get("latest_arrival_at_tuas", time_window_end)
        try:
            dt_end = _parse_dt(time_window_end)
            if dt_end is not None:
                latest_arrival = (dt_end - timedelta(minutes=30)).isoformat()
        except Exception:
            pass

        estimated_round_trip = transit_time * 2 + 30

        output: dict = {
            "status": "success",
            "terminal": terminal,
            "available_trucks": available,
            "total_fleet": total_fleet,
            "transit_time_minutes": transit_time,
            "road_conditions": road_conditions,
            "cost_per_trip": cost_per_trip,
            "lta_chassis_limits": lta_limits,
            "estimated_round_trip_minutes": estimated_round_trip,
            "estimated_round_trip": estimated_round_trip,
            "baseline_trips_all_120_containers": baseline_trips,
            "baseline_road_cost": baseline_cost,
            "baseline_road_cost_all_120": baseline_cost,
            "earliest_departure": earliest_departure,
            "latest_arrival": latest_arrival,
            "latest_arrival_at_tuas": latest_arrival,
            "capacity_ratio": capacity_ratio,
            "fleet_utilisation": fleet_utilisation,
            "fleet_utilisation_pct": fleet_utilisation,
            "esc_5_flag": esc_flag,
        }

        if esc_flag:
            esc = {
                "trigger_id": "esc_5",
                "name": "Road ITT capacity below threshold",
                "condition": f"available_trucks ({available}) < required_trips ({required_trips}) * 0.6 = {int(required_trips * 0.6)}",
                "threshold": 0.6,
                "rationale": "Insufficient road capacity — requires emergency sea ITT coordination",
                "recommendation": "Increase sea allocation in ITT split or escalate to duty manager",
            }
            output["escalation_flag"] = esc
            output["esc_5"] = esc

        return ToolResult(output=output, confidence=confidence, metadata={"peak_detected": peak})
