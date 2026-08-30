import asyncio

import pytest

from app.tools.base import BaseTool, ToolResult
from app.tools.registry import FALLBACKS, TOOLSETS, ToolRegistry, load_tools_for_problem, registry


class _DummyTool(BaseTool):
    name = "dummy_tool"
    description = "dummy"
    parameters_schema = {"type": "object", "properties": {"vessel_id": {"type": "string"}}, "required": ["vessel_id"]}

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(output={"ok": True, "vessel_id": kwargs["vessel_id"]}, confidence=0.95, metadata={})


def test_register_and_list():
    r = ToolRegistry()
    r.clear()
    assert r.list() == []
    t = _DummyTool()
    r.register(t)
    assert "dummy_tool" in r.list()
    assert r.get_tool("dummy_tool") is t
    assert len(r.get_schemas()) == 1
    assert r.get_schemas()[0]["name"] == "dummy_tool"


def test_register_many():
    r = ToolRegistry()
    r.clear()
    t1 = _DummyTool()
    t2 = _DummyTool()
    t2.name = "dummy_tool_2"
    r.register_many([t1, t2])
    assert set(r.list()) == {"dummy_tool", "dummy_tool_2"}


def test_clear():
    r = ToolRegistry()
    r.register(_DummyTool())
    r.clear()
    assert r.list() == []


def test_call_success():
    r = ToolRegistry()
    r.clear()
    r.register(_DummyTool())
    result = asyncio.run(r.call("dummy_tool", vessel_id="MV TEST", _run_id="run-123"))
    assert result.output["ok"] is True
    assert result.confidence == 0.95
    assert result.metadata["tool_name"] == "dummy_tool"
    assert result.metadata["run_id"] == "run-123"
    assert "timestamp" in result.metadata
    assert "duration_ms" in result.metadata


def test_call_missing_required():
    r = ToolRegistry()
    r.clear()
    r.register(_DummyTool())
    result = asyncio.run(r.call("dummy_tool", _run_id="run-x"))
    assert result.confidence == 0.0
    assert "error" in result.output
    assert result.metadata["error"] == "missing_required:vessel_id"


def test_call_hallucinated_arg():
    r = ToolRegistry()
    r.clear()
    r.register(_DummyTool())
    result = asyncio.run(r.call("dummy_tool", vessel_id="MV TEST", hallucinated_param="oops"))
    assert result.confidence == 0.0
    assert "error" in result.output
    assert "hallucinated_arg" in result.metadata["error"]


def test_call_hallucinated_tool():
    r = ToolRegistry()
    r.clear()
    result = asyncio.run(r.call("nonexistent_tool_xyz", _run_id="run-1"))
    assert result.confidence == 0.0
    assert "Unknown tool" in result.output["error"]
    assert result.metadata["error"] == "hallucinated"


def test_register_for_problem_pb12_to_pb01_to_pb12():
    r = ToolRegistry()
    r.register_for_problem("pb-12-itt")
    tools12 = set(r.list())
    assert "get_itt_candidates" in tools12
    assert "check_road_itt_capacity" in tools12
    assert len(tools12) == 8

    r.register_for_problem("pb-01-berth")
    tools01 = set(r.list())
    assert "query_vessel_arrival" in tools01
    assert "check_berth_availability" in tools01
    assert len(tools01) == 5
    assert tools01 != tools12

    r.register_for_problem("pb-12-itt")
    tools_back = set(r.list())
    assert tools_back == tools12


def test_register_for_problem_all_7():
    r = ToolRegistry()
    for pid in TOOLSETS.keys():
        r.register_for_problem(pid)
        tools = set(r.list())
        # Should have at least the tools from YAML (may have more than hardcoded TOOLSETS)
        assert len(tools) > 0, f"{pid} should have tools"
        # Check that key tools are present
        if pid == "pb-12-itt":
            assert "get_itt_candidates" in tools
            assert "check_road_itt_capacity" in tools
        elif pid == "pb-01-berth":
            assert "query_vessel_arrival" in tools
            assert "check_berth_availability" in tools
    r.register_for_problem("pb-12-itt")


def test_fallback_mapping_exists():
    assert FALLBACKS["check_road_itt_capacity"] == "cached_road_capacity"
    assert FALLBACKS["check_sea_itt_capacity"] == "cached_sea_capacity"
    from app.tools.fallbacks import CachedRoadCapacityTool, CachedSeaCapacityTool

    t1 = CachedRoadCapacityTool()
    r = asyncio.run(t1.call(_run_id="run-fb"))
    assert r.output["fallback_used"] is True
    assert r.metadata["fallback_used"] is True
    assert r.confidence == 0.6

    t2 = CachedSeaCapacityTool()
    r2 = asyncio.run(t2.call(_run_id="run-fb2"))
    assert r2.output["fallback_used"] is True
    assert r2.metadata["fallback_used"] is True


def test_singleton_import():
    from app.tools.registry import registry as reg2

    assert reg2 is registry
    reg2.clear()
    reg2.register_for_problem("pb-12-itt")
    assert "get_itt_candidates" in reg2.list()
    from app.tools.registry import registry as reg3

    assert reg3.list() == reg2.list()


def test_load_tools_for_problem_factory():
    tools = load_tools_for_problem("pb-12-itt")
    assert len(tools) == 8
    assert all(isinstance(t, BaseTool) for t in tools)
    assert {t.name for t in tools} == set(TOOLSETS["pb-12-itt"])


def test_toolresult_metadata_populated():
    r = ToolRegistry()
    r.clear()
    r.register(_DummyTool())
    result = asyncio.run(r.call("dummy_tool", vessel_id="MV X", _run_id="my-run"))
    assert result.metadata["tool_name"] == "dummy_tool"
    assert result.metadata["run_id"] == "my-run"
    assert isinstance(result.metadata["duration_ms"], int)
    assert "T" in result.metadata["timestamp"]


def test_get_schemas_after_register_for_problem():
    r = ToolRegistry()
    r.register_for_problem("pb-01-berth")
    schemas = r.get_schemas()
    assert len(schemas) == 5
    assert all("name" in s and "description" in s and "parameters" in s for s in schemas)


def test_timeout_handling():
    class SlowTool(BaseTool):
        name = "slow_tool"
        description = "slow"
        parameters_schema = {"type": "object", "properties": {}, "required": []}
        timeout_seconds = 1

        async def execute(self, **kwargs) -> ToolResult:
            await asyncio.sleep(5)
            return ToolResult(output={}, confidence=1.0, metadata={})

    r = ToolRegistry()
    r.clear()
    r.register(SlowTool())
    result = asyncio.run(r.call("slow_tool", _run_id="run-timeout"))
    assert result.confidence == 0.0
    assert "timed out" in result.output["error"]
    assert result.metadata["error"] == "timeout"


def test_yaml_charter_names_match_toolsets():
    from app.configs.problem_config import load_problem_config

    cfg = load_problem_config("pb-12-itt")
    yaml_tools = {t.name for t in cfg.tools if getattr(t, "type", None) != "event_trigger"}
    assert yaml_tools == set(TOOLSETS["pb-12-itt"]), f"YAML {yaml_tools} != TOOLSETS {set(TOOLSETS['pb-12-itt'])}"
    assert "receive_webhook" not in yaml_tools
    assert len(yaml_tools) == 8


def test_post_approval_guard_rejects_without_hitl():
    r = ToolRegistry()
    r.register_for_problem("pb-12-itt")
    result = asyncio.run(r.call("dispatch_road_itt", num_trucks=2, route="PPT → West Coast Highway → AYE → Tuas Port Boulevard", container_ids=["MSKU123"], _run_id="hitl-neg"))
    assert result.confidence == 0.0
    assert "HITL approval required" in result.output["error"]
    assert result.metadata["error"] == "hitl_required"
    result2 = asyncio.run(r.call("request_feeder_hold", feeder_id="FEEDER ATLANTIC-03", hold_hours=1, _run_id="hitl-neg2"))
    assert result2.confidence == 0.0
    assert result2.metadata["error"] == "hitl_required"
    ok = asyncio.run(r.call("dispatch_road_itt", num_trucks=2, route="x", container_ids=["a"], _run_id="hitl-ok", _hitl_approved=True))
    assert ok.confidence != 0.0 or "error" not in ok.output or "HITL" not in ok.output.get("error", "")
