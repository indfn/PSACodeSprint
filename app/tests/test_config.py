"""Tests for YAML config loading — all 7 C2 problems (F-04, F-10)."""

import pytest
from app.configs.problem_config import load_problem_config


def test_load_pb12_itt():
    c = load_problem_config("pb-12-itt")
    assert len(c.systems) == 5
    assert len(c.tools) == 6
    assert len(c.hitl_gates) == 5
    assert len(c.escalation_triggers) == 7
    assert c.confidence.enabled is True
    assert c.confidence.threshold == 0.85
    assert "road_cost_per_trip" in c.cost_params
    assert c.problem.id == "PB-12"


def test_load_pb12_short_id():
    c = load_problem_config("pb-12")
    assert c.problem.id == "PB-12"
    assert len(c.systems) == 5


def test_load_all_7_configs():
    # All 7 C2 problems must load without error
    ids = ["pb-01-berth", "pb-02-dtqc", "pb-04-feeder", "pb-09-expressway", "pb-10-sea-air", "pb-11-customs", "pb-12-itt"]
    for pid in ids:
        c = load_problem_config(pid)
        assert len(c.systems) >= 3, f"{pid} systems"
        assert len(c.tools) >= 5, f"{pid} tools"
        assert len(c.hitl_gates) >= 1, f"{pid} hitl_gates"


def test_missing_config_raises():
    with pytest.raises(FileNotFoundError):
        load_problem_config("pb-99-nonexistent")


def test_config_fields_have_defaults():
    # Sibling configs currently incomplete — should still load with defaults
    c = load_problem_config("pb-01-berth")
    # escalation_triggers may be empty before 4.7, but should not crash
    assert isinstance(c.escalation_triggers, list)
    assert isinstance(c.cost_params, dict)
    assert isinstance(c.constraints, dict)


def test_tools_have_tool_ids():
    for pid in ["pb-01-berth", "pb-12-itt"]:
        c = load_problem_config(pid)
        for t in c.tools:
            assert t.name, f"{pid} tool missing name"
            assert t.tool_id, f"{pid} tool {t.name} missing tool_id"


def test_systems_have_capabilities():
    c = load_problem_config("pb-12-itt")
    for s in c.systems:
        assert s.name
        assert s.type
        assert isinstance(s.capabilities, list)
