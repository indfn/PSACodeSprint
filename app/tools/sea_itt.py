from __future__ import annotations

from datetime import datetime, timedelta

from app.mocks.data import get_feeder_data
from app.tools.base import BaseTool, ToolResult


def _parse_dt(s: str | None) -> datetime:
    if not isinstance(s, str) or not s:
        raise ValueError(f"invalid datetime: {s!r}")
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


class SeaITTCapacityTool(BaseTool):
    name = "check_sea_itt_capacity"
    description = "Query PORTNET for feeder vessel availability, berth status, departure window, and downstream port tidal constraints"
    parameters_schema = {
        "type": "object",
        "properties": {
            "feeder_id": {"type": "string", "description": "Feeder vessel identifier e.g. FEEDER ATLANTIC-03"},
            "current_time": {"type": "string", "description": "ISO-8601 current timestamp for capacity check"},
        },
        "required": ["feeder_id", "current_time"],
    }
    fallback_tool = "cached_sea_capacity"
    timeout_seconds = 10

    async def execute(self, feeder_id: str, current_time: str, **kwargs) -> ToolResult:
        run_id = kwargs.get("_run_id", "") or kwargs.get("run_id", "")
        data = get_feeder_data(feeder_id=feeder_id, run_id=run_id)
        if not isinstance(data, dict) or data.get("status") != "success":
            return ToolResult(output={"status": "error", "error": f"Feeder '{feeder_id}' not found"}, confidence=0.0, metadata={})

        try:
            _parse_dt(current_time)
        except Exception as exc:
            return ToolResult(output={"status": "error", "error": f"Invalid current_time format: {exc}"}, confidence=0.0, metadata={})

        dep_window: dict = data.get("departure_window", {})
        downstream: dict | None = data.get("downstream_constraints")

        tidal_feasibility: dict | None = None
        tidal_risk: str = "unknown"
        latest_safe_departure: str | None = None
        margin_hours: float | None = None
        feasible: bool | None = None
        hold_scenarios: dict = {}
        confidence = 0.95

        if downstream and dep_window.get("latest") and downstream.get("tidal_window"):
            try:
                dep_latest = _parse_dt(dep_window["latest"])
                tidal_window = _parse_dt(downstream["tidal_window"])
                transit = float(downstream.get("transit_time_hours", 18))
                buffer = float(downstream.get("buffer_hours", 1.0))
                lsd = tidal_window - timedelta(hours=transit + buffer)
                latest_safe_departure = lsd.isoformat()
                margin = (lsd - dep_latest).total_seconds() / 3600
                margin_hours = round(margin, 2)
                if margin >= 2.0:
                    tidal_risk = "safe"
                    feasible = True
                    msg = f"Feeder can depart by {dep_window['latest']} and arrive at {downstream['destination_port']} well before tidal window at {downstream['tidal_window']}. Margin: {margin_hours:.1f} hrs."
                elif margin >= 1.0:
                    tidal_risk = "marginal"
                    feasible = True
                    msg = f"Feeder departure at {dep_window['latest']} leaves only {margin_hours:.1f} hrs margin before tidal window at {downstream['destination_port']}. Hold requests should be limited."
                elif margin >= 0:
                    tidal_risk = "critical"
                    feasible = True
                    msg = f"WARNING: Feeder departure at {dep_window['latest']} leaves only {margin_hours:.1f} hrs margin. Any delay will cause the feeder to miss the tidal window at {downstream['destination_port']}."
                else:
                    tidal_risk = "critical" if margin > -6 else "missed"
                    feasible = False
                    msg = f"ALERT: Feeder cannot catch the tidal window at {downstream['destination_port']}. Latest safe departure was {lsd.strftime('%H:%M')} but departure latest is {dep_window['latest']}."
                if tidal_risk == "missed":
                    tidal_risk = "critical"
                tidal_feasibility = {
                    "feasible": feasible,
                    "margin_hours": margin_hours,
                    "risk_level": tidal_risk,
                    "latest_safe_departure": latest_safe_departure,
                    "message": msg,
                }
                hold_cost = float(data.get("hold_cost_per_hour", 800))
                missed = float(data.get("missed_connection_cost", 5000))
                for h in [1, 2, 3, 6]:
                    new_dep = dep_latest + timedelta(hours=h)
                    new_margin = (lsd - new_dep).total_seconds() / 3600
                    if new_margin >= 1.0:
                        r = "safe" if new_margin >= 2.0 else "marginal"
                    elif new_margin >= 0:
                        r = "critical"
                    else:
                        r = "missed"
                    hold_scenarios[f"{h}h"] = {
                        "hold_hours": h,
                        "hold_cost": hold_cost * h,
                        "new_departure": new_dep.isoformat(),
                        "tidal_risk": r,
                        "margin_hours": round(new_margin, 2),
                    }
                berth = str(data.get("berth_status", ""))
                is_berthed = "berthed" in berth
                if tidal_risk == "safe" and is_berthed:
                    confidence = 0.95
                elif tidal_risk == "marginal":
                    confidence = 0.7
                elif tidal_risk in ("critical", "missed"):
                    confidence = 0.5
                elif not is_berthed:
                    confidence = 0.5
                else:
                    confidence = 0.7
            except Exception:
                tidal_feasibility = None
                tidal_risk = "unknown"
        else:
            tidal_feasibility = None

        berth_status = data.get("berth_status", "")
        output: dict = {
            "status": "success",
            "feeder_id": data.get("feeder_id", feeder_id),
            "feeder_operator": data.get("feeder_operator"),
            "vessel_type": data.get("vessel_type", "Feeder"),
            "capacity_teu": data.get("capacity_teu"),
            "current_occupancy_teu": data.get("current_occupancy_teu"),
            "available_capacity_teu": data.get("available_capacity_teu"),
            "available": data.get("available_capacity_teu"),
            "berth_status": berth_status,
            "departure_window": dep_window,
            "downstream_constraints": downstream,
            "downstream": downstream,
            "hold_cost_per_hour": data.get("hold_cost_per_hour"),
            "missed_connection_cost": data.get("missed_connection_cost"),
            "capacity": {
                "capacity_teu": data.get("capacity_teu"),
                "current_occupancy_teu": data.get("current_occupancy_teu"),
                "available_capacity_teu": data.get("available_capacity_teu"),
            },
            "is_berthed": "berthed" in str(berth_status),
            "tidal_risk": tidal_risk,
            "latest_safe_departure": latest_safe_departure,
            "margin_hours": margin_hours,
            "data_timestamp": current_time,
        }
        if tidal_feasibility is not None:
            output["tidal_feasibility"] = tidal_feasibility
        if hold_scenarios:
            output["hold_cost_scenarios"] = hold_scenarios
            output["hold_cost"] = hold_scenarios
        if downstream and downstream.get("must_depart_by"):
            output["must_depart_by"] = downstream["must_depart_by"]
        return ToolResult(output=output, confidence=confidence, metadata={"tidal_risk": tidal_risk})
