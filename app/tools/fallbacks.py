from __future__ import annotations

from app.tools.base import BaseTool, ToolResult
from app.mocks.data import get_feeder_data, get_truck_data


class CachedRoadCapacityTool(BaseTool):
    name = "cached_road_capacity"
    description = "Fallback: return last-known-good road capacity (conservative defaults)"
    parameters_schema = {
        "type": "object",
        "properties": {
            "terminal": {"type": "string"},
            "time_window_start": {"type": "string"},
            "time_window_end": {"type": "string"},
        },
        "required": [],
    }
    timeout_seconds = 10

    async def execute(self, **kwargs) -> ToolResult:
        data = get_truck_data(terminal=kwargs.get("terminal", "PPT"))
        output = {**data, "fallback_used": True, "fallback_source": "cached_road_capacity"}
        return ToolResult(
            output=output,
            confidence=0.6,
            metadata={"fallback_used": True, "fallback_for": "check_road_itt_capacity"},
        )


class CachedSeaCapacityTool(BaseTool):
    name = "cached_sea_capacity"
    description = "Fallback: return last-known-good sea capacity (conservative defaults)"
    parameters_schema = {
        "type": "object",
        "properties": {
            "feeder_id": {"type": "string"},
            "current_time": {"type": "string"},
        },
        "required": [],
    }
    timeout_seconds = 10

    async def execute(self, **kwargs) -> ToolResult:
        data = get_feeder_data(feeder_id=kwargs.get("feeder_id", "FEEDER ATLANTIC-03"))
        output = {**data, "fallback_used": True, "fallback_source": "cached_sea_capacity"}
        return ToolResult(
            output=output,
            confidence=0.6,
            metadata={"fallback_used": True, "fallback_for": "check_sea_itt_capacity"},
        )
