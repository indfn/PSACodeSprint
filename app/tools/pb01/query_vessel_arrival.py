from __future__ import annotations

from app.mocks.pb01_data import get_vessel_data
from app.tools.base import BaseTool, ToolResult


class QueryVesselArrivalTool(BaseTool):
    name = "query_vessel_arrival"
    description = "Query VTIS for vessel arrival ETA, pilot and tug availability"
    parameters_schema = {
        "type": "object",
        "properties": {
            "vessel_id": {"type": "string", "description": "Vessel ID"},
        },
        "required": ["vessel_id"],
    }
    timeout_seconds = 10

    async def execute(self, vessel_id: str, **kwargs) -> ToolResult:
        data = get_vessel_data(vessel_id)
        return ToolResult(output=data, confidence=0.95)
