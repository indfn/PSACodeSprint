"""Platform generalisation tests — 4.9 Cross-Check + Cost Params (F-11, F-12, F-13).

Fix: Removed module-level TestClient; now uses shared `client` fixture from
app/tests/conftest.py to avoid session-scoped state leakage.
"""

from app.agent.problem_switcher import get_active_problem_id, switch_problem
from app.configs.problem_config import load_problem_config


def test_load_all_7_configs_have_counts():
    expectations = {
        "pb-01-berth": {"systems": 3, "tools": 5, "gates": 2, "triggers": 7},
        "pb-02-dtqc": {"systems": 3, "tools": 5, "gates": 2, "triggers": 7},
        "pb-04-feeder": {"systems": 3, "tools": 5, "gates": 2, "triggers": 7},
        "pb-09-expressway": {"systems": 3, "tools": 5, "gates": 2, "triggers": 7},
        "pb-10-sea-air": {"systems": 3, "tools": 5, "gates": 2, "triggers": 7},
        "pb-11-customs": {"systems": 3, "tools": 5, "gates": 2, "triggers": 7},
        "pb-12-itt": {"systems": 5, "tools": 9, "gates": 5, "triggers": 7},
    }
    for pid, exp in expectations.items():
        cfg = load_problem_config(pid)
        assert len(cfg.systems) == exp["systems"], f"{pid} systems {len(cfg.systems)} != {exp['systems']}"
        assert len(cfg.tools) == exp["tools"], f"{pid} tools"
        assert len(cfg.hitl_gates) == exp["gates"], f"{pid} gates"
        assert len(cfg.escalation_triggers) == exp["triggers"], f"{pid} triggers"


def test_pb12_cost_params_10_rows():
    cfg = load_problem_config("pb-12-itt")
    cp = cfg.cost_params
    # Charter §5 10 rows must be present (at least 10 keys, specific values)
    assert len(cp) >= 10, f"pb-12 cost_params has {len(cp)} rows, need >=10"
    assert cp["road_cost_per_trip"] == 150
    assert cp["vessel_demurrage_per_hr"] == 2500
    assert cp["feeder_charter_per_hr"] == 800
    assert cp["sea_terminal_handling"] == 35
    assert cp["yard_rehandle"] == 35
    assert cp["missed_connection_per_container"] == 150
    assert cp["sea_marginal_charter_cost"] == 0
    assert cp["feeder_hold_cost_per_hr"] == 800
    assert cp["block_max_capacity_teu"] == 4500
    # LTA chassis is stored as string in cost or constraints
    assert "lta_chassis" in cfg.constraints or "lta_chassis_capacity" in cp


def test_all_cost_params_parsed():
    for pid in ["pb-01-berth", "pb-02-dtqc", "pb-04-feeder", "pb-09-expressway", "pb-10-sea-air", "pb-11-customs", "pb-12-itt"]:
        cfg = load_problem_config(pid)
        assert isinstance(cfg.cost_params, dict) and len(cfg.cost_params) >= 3, f"{pid} cost_params"
        assert isinstance(cfg.constraints, dict) and len(cfg.constraints) >= 3, f"{pid} constraints"
        assert isinstance(cfg.edge_cases, list) and len(cfg.edge_cases) >= 2, f"{pid} edge_cases"
        assert cfg.confidence.threshold == 0.85


def test_switch_pb12_to_pb01_tool_set_changes():
    cfg12 = switch_problem("pb-12-itt")
    tools12 = {t.name for t in cfg12.tools if getattr(t, "type", None) != "event_trigger"}
    assert "get_itt_candidates" in tools12
    assert "compute_itt_split" in tools12
    assert get_active_problem_id() == "pb-12-itt"

    cfg01 = switch_problem("pb-01-berth")
    tools01 = {t.name for t in cfg01.tools}
    assert "query_vessel_arrival" in tools01
    assert "compute_berth_reassignment" in tools01
    assert tools01 != tools12, "tool sets should differ after switch"
    assert get_active_problem_id() == "pb-01-berth"

    # Switch back
    cfg_back = switch_problem("pb-12-itt")
    tools_back = {t.name for t in cfg_back.tools if getattr(t, "type", None) != "event_trigger"}
    assert tools_back == tools12
    assert get_active_problem_id() == "pb-12-itt"


def test_switch_via_http(client):
    r = client.post("/agent/switch-problem/pb-01-berth")
    assert r.status_code == 200
    data = r.json()
    assert data["problem_id"] == "pb-01-berth"
    assert "vtis" in data["systems"]
    assert "query_vessel_arrival" in data["tools"]
    assert len(data["hitl_gates"]) == 2

    r2 = client.post("/agent/switch-problem/pb-12-itt")
    assert r2.status_code == 200
    data2 = r2.json()
    assert "citos_ppt" in data2["systems"]
    assert "get_itt_candidates" in data2["tools"]
    assert len(data2["hitl_gates"]) == 5
    # verify active-problem endpoint reflects latest
    r3 = client.get("/agent/active-problem")
    assert r3.json()["active_problem_id"] == "pb-12-itt"


def test_prompt_templated_from_config():
    # Simulate Phase 6.2 build_system_prompt(config) — must be templated, not hardcoded
    def build_system_prompt(cfg):
        return f"You are PSA Nexus coordinator for {cfg.problem.name} ({cfg.problem.id}) in {cfg.problem.sector}. Tools: {', '.join(t.name for t in cfg.tools)}"

    cfg12 = load_problem_config("pb-12-itt")
    p12 = build_system_prompt(cfg12)
    assert "Multi-Party ITT Coordination Failure" in p12
    assert "PB-12" in p12
    assert "get_itt_candidates" in p12

    cfg01 = load_problem_config("pb-01-berth")
    p01 = build_system_prompt(cfg01)
    assert "Berth Delay Cascade" in p01
    assert "PB-01" in p01
    assert "query_vessel_arrival" in p01
    assert p01 != p12


def test_tool_sets_change_after_http_switch(client):
    # Ensure tool sets reported via HTTP differ per problem (platform proof)
    r01 = client.post("/agent/switch-problem/pb-02-dtqc")
    tools01 = set(r01.json()["tools"])
    r12 = client.post("/agent/switch-problem/pb-12-itt")
    tools12 = set(r12.json()["tools"])
    assert tools01.isdisjoint(tools12) or tools01 != tools12
    # Reset to pb-12 for downstream tests
    switch_problem("pb-12-itt")
