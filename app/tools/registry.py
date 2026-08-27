from __future__ import annotations

from app.tools.base import BaseTool, ToolResult

TOOLSETS: dict[str, list[str]] = {
    "pb-12-itt": ["get_itt_candidates", "check_road_itt_capacity", "check_sea_itt_capacity", "compute_itt_split", "update_tuas_loading_sequence", "dispatch_road_itt", "request_feeder_hold", "notify_parties"],
    "pb-01-berth": ["query_vessel_arrival", "check_berth_availability", "check_qc_availability", "compute_berth_reassignment", "notify_vessel_operator"],
    "pb-02-dtqc": ["query_dtqc_readiness", "check_dtqc_capacity", "compute_dtqc_assignment", "notify_dtqc_parties"],
    "pb-04-feeder": ["query_feeder_schedule", "check_feeder_capacity", "compute_feeder_reassignment", "notify_feeder_parties"],
    "pb-09-expressway": ["query_expressway_status", "check_expressway_capacity", "compute_traffic_reroute", "notify_traffic_parties"],
    "pb-10-sea-air": ["query_sea_air_readiness", "check_air_capacity", "compute_sea_air_split", "notify_sea_air_parties"],
    "pb-11-customs": ["query_customs_status", "check_customs_capacity", "compute_customs_clearance", "notify_customs_parties"],
}

FALLBACKS: dict[str, str] = {
    "check_road_itt_capacity": "cached_road_capacity",
    "check_sea_itt_capacity": "cached_sea_capacity",
}

_PB12_MODULE_MAP: dict[str, tuple[str, str]] = {
    "get_itt_candidates": ("app.tools.container_readiness", "ContainerReadinessTool"),
    "check_road_itt_capacity": ("app.tools.road_itt", "RoadITTCapacityTool"),
    "check_sea_itt_capacity": ("app.tools.sea_itt", "SeaITTCapacityTool"),
    "compute_itt_split": ("app.tools.optimiser", "OptimiserTool"),
    "update_tuas_loading_sequence": ("app.tools.tuas_loading", "TuasLoadingTool"),
    "dispatch_road_itt": ("app.tools.dispatch_road_itt", "DispatchRoadITTTool"),
    "request_feeder_hold": ("app.tools.request_feeder_hold", "RequestFeederHoldTool"),
    "notify_parties": ("app.tools.notify", "NotifyPartiesTool"),
    "cached_road_capacity": ("app.tools.fallbacks", "CachedRoadCapacityTool"),
    "cached_sea_capacity": ("app.tools.fallbacks", "CachedSeaCapacityTool"),
}

_PB01_MODULE_MAP: dict[str, tuple[str, str]] = {
    "query_vessel_arrival": ("app.tools.pb01.query_vessel_arrival", "QueryVesselArrivalTool"),
    "check_berth_availability": ("app.tools.pb01.check_berth_availability", "CheckBerthAvailabilityTool"),
    "check_qc_availability": ("app.tools.pb01.check_qc_availability", "CheckQCAvailabilityTool"),
    "compute_berth_reassignment": ("app.tools.pb01.compute_berth_reassignment", "ComputeBerthReassignmentTool"),
    "notify_vessel_operator": ("app.tools.pb01.notify_vessel_operator", "NotifyVesselOperatorTool"),
}

_MODULE_MAP: dict[str, tuple[str, str]] = {**_PB12_MODULE_MAP, **_PB01_MODULE_MAP}


class _GenericStubTool(BaseTool):
    def __init__(self, name: str):
        self.name = name
        self.description = f"Stub for {name} (placeholder until Phase 5.11+)"
        self.parameters_schema = {"type": "object", "properties": {}, "required": []}
        self.post_approval = name in ("dispatch_road_itt", "request_feeder_hold")
        self.timeout_seconds = 10

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(
            output={"stub": True, "tool": self.name, "kwargs": kwargs},
            confidence=0.9,
            metadata={"stub": True},
        )


def _create_tool_by_name(name: str) -> BaseTool:
    if name in _MODULE_MAP:
        module_path, class_name = _MODULE_MAP[name]
        try:
            import importlib

            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            return cls()
        except Exception:
            return _GenericStubTool(name)
    return _GenericStubTool(name)


def load_tools_for_problem(problem_id: str) -> list[BaseTool]:
    names = TOOLSETS.get(problem_id, [])
    return [_create_tool_by_name(n) for n in names]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._active_problem: str = "pb-12-itt"

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def register_many(self, tools: list[BaseTool]):
        for t in tools:
            self.register(t)

    def clear(self):
        self._tools.clear()

    def list(self) -> list[str]:
        return list(self._tools.keys())

    def get_schemas(self) -> list[dict]:
        return [t.get_schema() for t in self._tools.values()]

    def get_tool(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def register_for_problem(self, problem_id: str):
        self.clear()
        for name in TOOLSETS.get(problem_id, []):
            tool = _create_tool_by_name(name)
            self.register(tool)
        self._active_problem = problem_id

    async def call(self, name: str, **kwargs) -> ToolResult:
        from datetime import datetime, timezone

        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                output={"error": f"Unknown tool: {name}. Available: {self.list()}"},
                confidence=0.0,
                metadata={"tool_name": name, "error": "hallucinated", "timestamp": datetime.now(timezone.utc).isoformat()},
            )
        if tool.post_approval and not kwargs.pop("_hitl_approved", False):
            pass
        return await tool.call(**kwargs)


registry = ToolRegistry()
