from __future__ import annotations

from app.mocks.pb01_data import get_qc_data
from app.tools.base import BaseTool, ToolResult


class CheckQCAvailabilityTool(BaseTool):
    name = "check_qc_availability"
    description = "Query CITOS for QC count and crane status at berth"
    parameters_schema = {
        "type": "object",
        "properties": {
            "berth_id": {"type": "string", "description": "Berth ID"},
        },
        "required": ["berth_id"],
    }
    timeout_seconds = 10

    async def execute(self, berth_id: str, **kwargs) -> ToolResult:
        data = get_qc_data(berth_id)
        return ToolResult(output=data, confidence=0.92)
