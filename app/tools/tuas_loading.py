from __future__ import annotations

from app.mocks.data import get_loading_sequence_data
from app.tools.base import BaseTool, ToolResult


class TuasLoadingTool(BaseTool):
    name = "update_tuas_loading_sequence"
    description = "Update Tuas QC loading sequence based on ITT arrival predictions"
    parameters_schema = {
        "type": "object",
        "properties": {
            "vessel_id": {"type": "string", "description": "Vessel ID e.g. MV PACIFIC STAR"},
            "itt_eta_road": {"type": "string", "description": "ISO8601 ETA for road ITT arrival e.g. 2026-08-19T14:30:00+08:00", "format": "date-time"},
            "itt_eta_sea": {"type": "string", "description": "ISO8601 ETA for sea ITT arrival e.g. 2026-08-19T16:30:00+08:00", "format": "date-time"},
            "container_ids_road": {"type": "array", "items": {"type": "string"}, "description": "List of container IDs arriving via road ITT"},
            "container_ids_sea": {"type": "array", "items": {"type": "string"}, "description": "List of container IDs arriving via sea ITT"},
        },
        "required": ["vessel_id", "itt_eta_road", "itt_eta_sea", "container_ids_road", "container_ids_sea"],
    }
    timeout_seconds = 10

    async def execute(
        self,
        vessel_id: str,
        itt_eta_road: str,
        itt_eta_sea: str,
        container_ids_road: list[str],
        container_ids_sea: list[str],
        **kwargs,
    ) -> ToolResult:
        data = get_loading_sequence_data(
            vessel_id=vessel_id,
            itt_eta_road=itt_eta_road,
            itt_eta_sea=itt_eta_sea,
        )
        output = {
            **data,
            "road_container_count": len(container_ids_road),
            "sea_container_count": len(container_ids_sea),
            "total_itt_containers": len(container_ids_road) + len(container_ids_sea),
        }
        return ToolResult(output=output, confidence=0.95)
