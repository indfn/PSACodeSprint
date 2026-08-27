from __future__ import annotations

from app.mocks.pb01_data import compute_berth_reassignment_data
from app.tools.base import BaseTool, ToolResult


class ComputeBerthReassignmentTool(BaseTool):
    name = "compute_berth_reassignment"
    description = "Run mock optimiser for berth reassignment — new berth + QC allocation"
    parameters_schema = {
        "type": "object",
        "properties": {
            "vessel_id": {"type": "string", "description": "Vessel ID"},
            "constraints": {"type": "object", "description": "Optional constraints overrides"},
        },
        "required": ["vessel_id"],
    }
    timeout_seconds = 10

    async def execute(self, vessel_id: str, constraints: dict | None = None, **kwargs) -> ToolResult:
        data = compute_berth_reassignment_data(vessel_id, constraints)
        return ToolResult(output=data, confidence=0.88)
