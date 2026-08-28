from __future__ import annotations

from app.mocks.data import get_container_data
from app.tools.base import BaseTool, ToolResult


class ContainerReadinessTool(BaseTool):
    name = "get_itt_candidates"
    description = "Query PPT CITOS for container readiness status"
    parameters_schema = {
        "type": "object",
        "properties": {
            "vessel_id": {"type": "string", "description": "Vessel ID"}
        },
        "required": ["vessel_id"],
    }
    timeout_seconds = 10

    async def execute(self, vessel_id: str = "MV PACIFIC STAR", **kwargs) -> ToolResult:
        run_id = kwargs.get("_run_id", "") or kwargs.get("run_id", "")
        data = get_container_data(vessel_id, run_id=run_id)
        confidence = 0.95
        if isinstance(data, dict) and "data_age_minutes" in data:
            age = data["data_age_minutes"]
            if age > 30:
                confidence = 0.6
            elif age > 5:
                confidence = 0.8
        return ToolResult(output=data, confidence=confidence)
