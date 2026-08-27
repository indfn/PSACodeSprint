from __future__ import annotations

from datetime import datetime, timedelta

from app.mocks.data import COST_PARAMS, FEEDER_DATA, get_feeder_data
from app.tools.base import BaseTool, ToolResult


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


class RequestFeederHoldTool(BaseTool):
    name = "request_feeder_hold"
    description = "Request feeder vessel hold via PORTNET. Requires HITL Gate 3 approval. NOTE: This is a REQUEST \u2014 feeder operator may decline."
    parameters_schema = {
        "type": "object",
        "properties": {
            "feeder_id": {"type": "string", "description": "Feeder vessel identifier e.g. FEEDER ATLANTIC-03"},
            "hold_hours": {"type": "number", "description": "Hold duration in hours (0.5-6)", "minimum": 0.5, "maximum": 6},
        },
        "required": ["feeder_id", "hold_hours"],
    }
    post_approval = True
    fallback_tool = None
    timeout_seconds = 10

    async def execute(self, feeder_id: str, hold_hours: float, **kwargs) -> ToolResult:
        if not isinstance(feeder_id, str) or not feeder_id.strip():
            return ToolResult(output={"error": "feeder_id must be non-empty", "status": "error"}, confidence=0.0, metadata={"error": "invalid_feeder_id"})
        try:
            hold_hours_f = float(hold_hours)
        except Exception:
            return ToolResult(output={"error": "hold_hours must be a number", "status": "error"}, confidence=0.0, metadata={"error": "invalid_hold_hours"})
        if hold_hours_f < 0.5 or hold_hours_f > 6:
            return ToolResult(output={"error": "hold_hours must be between 0.5 and 6", "status": "error"}, confidence=0.0, metadata={"error": "hold_hours_out_of_range"})

        data = get_feeder_data(feeder_id=feeder_id)
        dep_window = data.get("departure_window", {}) if isinstance(data, dict) else {}
        downstream = data.get("downstream_constraints", {}) if isinstance(data, dict) else {}
        latest_str = dep_window.get("latest") or dep_window.get("earliest") or "2026-08-19T16:00:00+08:00"
        try:
            latest_dt = _parse_dt(latest_str)
        except Exception:
            latest_dt = _parse_dt("2026-08-19T16:00:00+08:00")

        new_departure_dt = latest_dt + timedelta(hours=hold_hours_f)
        new_departure = new_departure_dt.isoformat()

        tidal_risk = "safe"
        try:
            tidal_str = downstream.get("tidal_window") if isinstance(downstream, dict) else None
            if tidal_str:
                tidal_dt = _parse_dt(tidal_str)
                transit = float(downstream.get("transit_time_hours", 18)) if isinstance(downstream, dict) else 18.0
                buffer_h = float(downstream.get("buffer_hours", 1.0)) if isinstance(downstream, dict) else 1.0
                lsd = tidal_dt - timedelta(hours=transit + buffer_h)
                margin = (lsd - new_departure_dt).total_seconds() / 3600
                if margin >= 2.0:
                    tidal_risk = "safe"
                elif margin >= 1.0:
                    tidal_risk = "marginal"
                elif margin >= 0:
                    tidal_risk = "critical"
                else:
                    tidal_risk = "critical"
                within_1h = abs((tidal_dt - new_departure_dt).total_seconds()) / 3600 <= 1.0
                if within_1h and tidal_risk != "critical":
                    tidal_risk = "critical"
            else:
                tidal_risk = "safe" if hold_hours_f <= 1.5 else "marginal" if hold_hours_f <= 3 else "critical"
        except Exception:
            tidal_risk = "safe" if hold_hours_f <= 1.5 else "marginal" if hold_hours_f <= 3 else "critical"

        declined = ("DECLINE" in feeder_id.upper()) or (hold_hours_f > 4)
        if declined:
            operator_response = "declined"
            status = "declined"
            reason = "Operator declined \u2014 tidal window risk"
            confidence = 0.5
        else:
            operator_response = "accepted"
            status = "accepted"
            reason = "Operator accepted hold request"
            confidence = 0.9

        hold_cost = hold_hours_f * float(COST_PARAMS.get("feeder_charter_per_hr", 800))
        output = {
            "status": status,
            "feeder_id": feeder_id,
            "hold_hours": hold_hours_f,
            "hold_cost": hold_cost,
            "hold_cost_per_hour": float(COST_PARAMS.get("feeder_charter_per_hr", 800)),
            "new_departure": new_departure,
            "previous_departure": latest_str,
            "tidal_risk": tidal_risk,
            "operator_response": operator_response,
            "reason": reason,
            "downstream_tidal": downstream.get("tidal_window") if isinstance(downstream, dict) else None,
        }
        return ToolResult(output=output, confidence=confidence, metadata={"tidal_risk": tidal_risk, "operator_response": operator_response})
