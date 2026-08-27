from __future__ import annotations

from datetime import datetime, timezone

from app.mocks.pb01_data import log_vessel_notification
from app.tools.base import BaseTool, ToolResult


class NotifyVesselOperatorTool(BaseTool):
    name = "notify_vessel_operator"
    description = "Notify vessel operator via VTIS of berth reassignment or delay"
    parameters_schema = {
        "type": "object",
        "properties": {
            "vessel_id": {"type": "string", "description": "Vessel ID"},
            "message": {"type": "string", "description": "Notification message"},
        },
        "required": ["vessel_id", "message"],
    }
    timeout_seconds = 10

    async def execute(self, vessel_id: str, message: str, **kwargs) -> ToolResult:
        entry = log_vessel_notification(vessel_id, message)
        output = {
            "notified": vessel_id,
            "vessel_id": vessel_id,
            "message": message,
            "timestamp": entry["timestamp"],
            "status": "sent",
        }
        return ToolResult(output=output, confidence=1.0)
