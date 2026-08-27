from __future__ import annotations

from app.mocks.pb01_data import get_berth_data
from app.tools.base import BaseTool, ToolResult


class CheckBerthAvailabilityTool(BaseTool):
    name = "check_berth_availability"
    description = "Query OptEVoyage for berth window, draft limit and tidal window"
    parameters_schema = {
        "type": "object",
        "properties": {
            "vessel_id": {"type": "string", "description": "Vessel ID"},
            "berth_id": {"type": "string", "description": "Berth ID"},
        },
        "required": ["berth_id"],
    }
    timeout_seconds = 10

    async def execute(self, berth_id: str, vessel_id: str = "MV EVER GIVEN", **kwargs) -> ToolResult:
        data = get_berth_data(vessel_id, berth_id)
        return ToolResult(output=data, confidence=0.9)
