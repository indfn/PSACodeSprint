from __future__ import annotations

import copy

from app.tools.base import BaseTool, ToolResult

# Lazy snapshots — refreshed on each call to avoid stale import-time data
_last_truck_snapshot: dict | None = None
_last_feeder_snapshot: dict | None = None


def _get_truck_snapshot() -> dict:
    global _last_truck_snapshot
    if _last_truck_snapshot is None:
        from app.mocks.data import get_truck_data
        _last_truck_snapshot = copy.deepcopy(get_truck_data())
    return _last_truck_snapshot


def _get_feeder_snapshot() -> dict:
    global _last_feeder_snapshot
    if _last_feeder_snapshot is None:
        from app.mocks.data import get_feeder_data
        _last_feeder_snapshot = copy.deepcopy(get_feeder_data())
    return _last_feeder_snapshot


def update_fallback_snapshots() -> None:
    """Refresh fallback snapshots with current mock data (call after edge injection / reset)."""
    global _last_truck_snapshot, _last_feeder_snapshot
    from app.mocks.data import get_truck_data, get_feeder_data
    _last_truck_snapshot = copy.deepcopy(get_truck_data())
    _last_feeder_snapshot = copy.deepcopy(get_feeder_data())


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
        data = copy.deepcopy(_get_truck_snapshot())
        if kwargs.get("terminal"):
            data["terminal"] = kwargs["terminal"]
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
        data = copy.deepcopy(_get_feeder_snapshot())
        if kwargs.get("feeder_id"):
            data["feeder_id"] = kwargs["feeder_id"]
        output = {**data, "fallback_used": True, "fallback_source": "cached_sea_capacity"}
        return ToolResult(
            output=output,
            confidence=0.6,
            metadata={"fallback_used": True, "fallback_for": "check_sea_itt_capacity"},
        )
