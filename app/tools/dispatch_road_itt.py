from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

from app.mocks.data import COST_PARAMS, generate_containers
from app.tools.base import BaseTool, ToolResult

_SIZE_MAP: dict[str, str] | None = None


def _get_size_map() -> dict[str, str]:
    global _SIZE_MAP
    if _SIZE_MAP is None:
        try:
            containers = generate_containers()
            _SIZE_MAP = {c["container_id"]: c["size"] for c in containers}
        except Exception:
            _SIZE_MAP = {}
    return _SIZE_MAP


def _compute_trips(container_ids: list[str]) -> int:
    size_map = _get_size_map()
    count_40 = 0
    count_20 = 0
    unknown = 0
    for cid in container_ids:
        size = size_map.get(cid)
        if size == "40ft":
            count_40 += 1
        elif size == "20ft":
            count_20 += 1
        else:
            unknown += 1
    if unknown and not (count_40 or count_20):
        return math.ceil(unknown / 1.5) if unknown else 0
    if unknown:
        count_20 += unknown
    return count_40 + math.ceil(count_20 / 2) if (count_40 or count_20) else 0


class DispatchRoadITTTool(BaseTool):
    name = "dispatch_road_itt"
    description = "Dispatch prime movers via OptETruck for road ITT. Requires HITL Gate 2 approval. Route: PPT \u2192 West Coast Highway \u2192 AYE \u2192 Tuas Port Boulevard."
    parameters_schema = {
        "type": "object",
        "properties": {
            "num_trucks": {"type": "integer", "description": "Number of prime movers to dispatch", "minimum": 1},
            "route": {"type": "string", "description": "Road route e.g. PPT \u2192 West Coast Highway \u2192 AYE \u2192 Tuas Port Boulevard"},
            "container_ids": {"type": "array", "items": {"type": "string"}, "description": "Container IDs to dispatch via road ITT"},
        },
        "required": ["num_trucks", "route", "container_ids"],
    }
    post_approval = True
    fallback_tool = None
    timeout_seconds = 10

    async def execute(self, num_trucks: int, route: str, container_ids: list[str], **kwargs) -> ToolResult:
        if not isinstance(num_trucks, int) or num_trucks <= 0:
            return ToolResult(output={"error": "num_trucks must be > 0", "status": "error"}, confidence=0.0, metadata={"error": "invalid_num_trucks"})
        if not isinstance(container_ids, list) or len(container_ids) == 0:
            return ToolResult(output={"error": "container_ids must be non-empty", "status": "error"}, confidence=0.0, metadata={"error": "empty_container_ids"})
        if not isinstance(route, str) or not route.strip():
            return ToolResult(output={"error": "route must be non-empty string", "status": "error"}, confidence=0.0, metadata={"error": "invalid_route"})

        cost_per_trip = COST_PARAMS.get("road_cost_per_trip", 150)
        total_trips = _compute_trips(container_ids)
        if total_trips == 0:
            total_trips = max(1, math.ceil(len(container_ids) / 2))

        dispatch_id = f"DISP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        eta = "2026-08-19T14:30:00+08:00"

        n = len(container_ids)
        chunk_size = math.ceil(n / num_trucks) if num_trucks else n
        truck_assignments: list[dict] = []
        for i in range(num_trucks):
            start = i * chunk_size
            end = min(start + chunk_size, n)
            chunk = container_ids[start:end] if start < n else []
            trips_for_truck = _compute_trips(chunk) if chunk else 0
            if not chunk:
                trips_for_truck = 0
            truck_assignments.append({
                "truck_id": f"TRUCK-{i+1:03d}",
                "containers": chunk,
                "container_count": len(chunk),
                "trips": trips_for_truck,
                "containers_per_trip": f"1x40ft OR 2x20ft" if trips_for_truck else "none",
            })

        cost = total_trips * cost_per_trip
        container_ids_truncated = container_ids[:5] if len(container_ids) > 5 else list(container_ids)
        truncated_note = f"showing {len(container_ids_truncated)}/{len(container_ids)}" if len(container_ids) > 5 else "all"

        output = {
            "status": "dispatched",
            "dispatch_id": dispatch_id,
            "num_trucks": num_trucks,
            "route": route,
            "container_ids": list(container_ids),
            "container_ids_truncated": container_ids_truncated,
            "truncated_note": truncated_note,
            "container_count": len(container_ids),
            "total_trips": total_trips,
            "truck_assignments": truck_assignments,
            "eta": eta,
            "cost": cost,
            "cost_per_trip": cost_per_trip,
            "total_cost": cost,
        }
        return ToolResult(output=output, confidence=0.95, metadata={"dispatched": True})
