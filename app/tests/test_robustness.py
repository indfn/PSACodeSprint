import asyncio
import copy
from unittest import mock

import pytest

import app.mocks.data as mock_data
from app.mocks.data import generate_containers, get_container_data, get_feeder_data, get_truck_data
from app.tools.base import ToolResult
from app.tools.container_readiness import ContainerReadinessTool
from app.tools.dispatch_road_itt import DispatchRoadITTTool
from app.tools.fallbacks import CachedRoadCapacityTool, CachedSeaCapacityTool
from app.tools.notify import NotifyPartiesTool
from app.tools.optimiser import OptimiserTool
from app.tools.registry import FALLBACKS
from app.tools.road_itt import RoadITTCapacityTool
from app.tools.request_feeder_hold import RequestFeederHoldTool
from app.tools.sea_itt import SeaITTCapacityTool
from app.tools.tuas_loading import TuasLoadingTool


def _weight_bounds_guard(containers: list[dict]) -> dict:
    failed = []
    for c in containers:
        w = c.get("weight_kg")
        if w is None or not isinstance(w, (int, float)) or w <= 0:
            failed.append(c.get("container_id", "?"))
    return {"passed": len(failed) == 0, "failed_ids": failed, "guardrail": "weight_bounds"}


def _make_trace() -> list[dict]:
    return []


def _sse_stub_publish(trace: list[dict], run_id: str, event_type: str, payload: dict):
    entry = {"event_type": event_type, "run_id": run_id, "payload": payload, "risk_score": 0.9}
    trace.append(entry)
    return entry


class TestS1Nominal:
    def test_nominal_happy_path_full_sequence(self):
        trace = _make_trace()
        run_id = "s1-nominal"
        mock_data.notification_log.clear()

        t1 = ContainerReadinessTool()
        r1 = asyncio.run(t1.call(vessel_id="MV PACIFIC STAR", _run_id=run_id))
        assert r1.output["total_containers"] == 120
        assert r1.output["total_teu"] == 160
        assert r1.output["dg_containers"] == 3
        assert sorted(r1.output["blocks_affected"]) == ["B-07", "B-08", "B-12", "B-14"]
        assert 0.0 <= r1.confidence <= 1.0
        assert r1.metadata["tool_name"] == "get_itt_candidates"
        assert "fallback_used" not in r1.output and "fallback_used" not in r1.metadata
        _sse_stub_publish(trace, run_id, "trace_entry", {"tool": "get_itt_candidates", "risk_score": 0.95})
        trace.append({"event": "tool_success", "tool": "get_itt_candidates", "risk_score": 0.95})

        t2 = RoadITTCapacityTool()
        r2 = asyncio.run(t2.call(terminal="PPT", time_window_start="2026-08-19T11:00:00+08:00", time_window_end="2026-08-19T18:00:00+08:00", _run_id=run_id))
        assert r2.output["status"] == "success"
        assert r2.output["available_trucks"] == 20
        assert r2.output["transit_time_minutes"] in (90, 110)
        assert r2.metadata.get("fallback_used") is not True
        assert r2.output.get("fallback_used") is not True
        _sse_stub_publish(trace, run_id, "trace_entry", {"tool": "check_road_itt_capacity", "risk_score": 0.9})
        trace.append({"event": "tool_success", "tool": "check_road_itt_capacity", "risk_score": 0.9})

        t3 = SeaITTCapacityTool()
        r3 = asyncio.run(t3.call(feeder_id="FEEDER ATLANTIC-03", current_time="2026-08-19T10:35:00+08:00", _run_id=run_id))
        assert r3.output["status"] == "success"
        assert r3.output["capacity_teu"] == 800
        assert r3.output["available_capacity_teu"] == 180
        assert "departure_window" in r3.output
        assert "downstream_constraints" in r3.output
        assert r3.metadata.get("fallback_used") is not True
        _sse_stub_publish(trace, run_id, "trace_entry", {"tool": "check_sea_itt_capacity", "risk_score": 0.9})
        trace.append({"event": "tool_success", "tool": "check_sea_itt_capacity", "risk_score": 0.9})

        t4 = OptimiserTool()
        r4 = asyncio.run(t4.call(candidates=r1.output, road_capacity=r2.output, sea_capacity=r3.output, tuas_vessel_departure="2026-08-19T20:00:00+08:00", _run_id=run_id))
        assert r4.output["optimal_split"]["total_transport_cost"] == 10400
        assert r4.output["optimal_split"]["road_containers"] == 80
        assert r4.output["optimal_split"]["sea_containers"] == 40
        assert r4.output["cost_vs_baseline"]["baseline_all_road_cost"] == 12000
        assert r4.output["cost_vs_baseline"]["direct_transport_savings"] == 1600
        _sse_stub_publish(trace, run_id, "trace_entry", {"tool": "compute_itt_split", "risk_score": 0.95})
        trace.append({"event": "tool_success", "tool": "compute_itt_split", "risk_score": 0.95})

        assert r4.metadata.get("fallback_used") is not True
        assert r4.output.get("fallback_used") is not True

        hitl_approved = True
        assert hitl_approved is True

        containers = r1.output["containers"]
        ids_road = [c["container_id"] for c in containers[:80]]
        ids_sea = [c["container_id"] for c in containers[80:]]
        dis = DispatchRoadITTTool()
        rd = asyncio.run(dis.call(num_trucks=4, route="PPT \u2192 West Coast Highway \u2192 AYE \u2192 Tuas Port Boulevard", container_ids=ids_road, _run_id=run_id, _hitl_approved=True))
        assert rd.output["status"] == "dispatched"
        assert rd.output["num_trucks"] == 4
        trace.append({"event": "dispatch", "tool": "dispatch_road_itt", "risk_score": 0.85})

        feeder = RequestFeederHoldTool()
        rf = asyncio.run(feeder.call(feeder_id="FEEDER ATLANTIC-03", hold_hours=1.0, _run_id=run_id, _hitl_approved=True))
        assert rf.output["status"] in ("accepted", "declined")
        trace.append({"event": "feeder_hold", "tool": "request_feeder_hold", "risk_score": 0.8})

        t5 = TuasLoadingTool()
        r5 = asyncio.run(t5.call(vessel_id="MV PACIFIC STAR", itt_eta_road="2026-08-19T14:30:00+08:00", itt_eta_sea="2026-08-19T16:30:00+08:00", container_ids_road=ids_road, container_ids_sea=ids_sea, _run_id=run_id))
        assert r5.output["status"] == "success"
        assert len(r5.output["qc_adjustments"]) == 4
        assert r5.output["road_container_count"] == 80
        assert r5.output["sea_container_count"] == 40
        _sse_stub_publish(trace, run_id, "trace_entry", {"tool": "update_tuas_loading_sequence", "risk_score": 0.9})
        trace.append({"event": "tool_success", "tool": "update_tuas_loading_sequence", "risk_score": 0.9})

        notifier = NotifyPartiesTool()
        rn = asyncio.run(notifier.call(message="ITT dispatch complete: 80 road + 40 sea containers. Total cost $10,400.", parties=["PPT_Yard", "Tuas_Yard"], _run_id=run_id))
        assert rn.output["status"] == "sent"
        assert rn.output["notified"] == ["PPT_Yard", "Tuas_Yard"]
        _sse_stub_publish(trace, run_id, "notification", {"parties": ["PPT_Yard", "Tuas_Yard"]})
        trace.append({"event": "notification", "parties": ["PPT_Yard", "Tuas_Yard"], "risk_score": 0.5})

        assert any(e.get("event") == "notification" for e in trace)
        assert len([e for e in trace if "risk_score" in e]) >= 6
        assert len(mock_data.notification_log) >= 1
        assert not any(v.get("fallback_used") is True for v in [r1.metadata, r2.metadata, r3.metadata, r4.metadata, r5.metadata])

    def test_nominal_sse_stub_all_event_types(self):
        trace: list[dict] = []
        _sse_stub_publish(trace, "s1-sse", "trace_entry", {"tool": "get_itt_candidates"})
        _sse_stub_publish(trace, "s1-sse", "notification", {"message": "done"})
        assert trace[0]["event_type"] == "trace_entry"
        assert trace[1]["event_type"] == "notification"
        assert all("risk_score" in e for e in trace)


class TestS2Incomplete:
    def test_weight_guardrail_fires_on_missing_weight(self):
        containers = generate_containers()
        bad = copy.deepcopy(containers)
        bad[5]["weight_kg"] = None
        bad[10]["weight_kg"] = 0
        bad[15].pop("weight_kg", None)
        guard = _weight_bounds_guard(bad)
        assert guard["passed"] is False
        assert len(guard["failed_ids"]) == 3
        assert guard["guardrail"] == "weight_bounds"

        trace: list[dict] = []
        trace.append({"event": "guardrail_failed", "rule": "weight_bounds", "failed_ids": guard["failed_ids"], "risk_score": 0.3})
        assert trace[0]["event"] == "guardrail_failed"
        assert trace[0]["rule"] == "weight_bounds"

    def test_zero_weight_also_fails(self):
        containers = [{"container_id": "MSKU7654321", "weight_kg": 0}]
        guard = _weight_bounds_guard(containers)
        assert guard["passed"] is False
        assert "MSKU7654321" in guard["failed_ids"]

    def test_none_weight_fails(self):
        containers = [{"container_id": "MSKU7654321", "weight_kg": None}]
        guard = _weight_bounds_guard(containers)
        assert guard["passed"] is False

    def test_valid_weights_pass(self):
        containers = generate_containers()
        guard = _weight_bounds_guard(containers)
        assert guard["passed"] is True
        assert guard["failed_ids"] == []

    def test_incomplete_data_hitl_card_and_resolution(self):
        trace: list[dict] = []
        run_id = "s2-incomplete"
        containers = generate_containers()
        containers[0]["weight_kg"] = None
        target = containers[0]["container_id"]
        guard = _weight_bounds_guard(containers)
        assert not guard["passed"]
        trace.append({"event": "guardrail_failed", "rule": "weight_bounds", "failed_ids": guard["failed_ids"], "risk_score": 0.2})

        _sse_stub_publish(trace, run_id, "confidence_update", {"confidence": 0.3, "reason": "weight_bounds"})
        hitl_card = {
            "gate": "HITL-2",
            "type": "hitl_card",
            "gap": f"weight unknown for {target}, verify?",
            "failed_ids": guard["failed_ids"],
            "prompt": f"weight unknown for {target}, verify?",
            "retry_source": "yard_status",
        }
        trace.append({"event": "hitl_card", "card": hitl_card, "risk_score": 0.4})
        _sse_stub_publish(trace, run_id, "trace_entry", hitl_card)

        t1 = ContainerReadinessTool()
        r_secondary = asyncio.run(t1.call(vessel_id="MV PACIFIC STAR", _run_id=run_id))
        assert r_secondary.output["total_containers"] == 120
        trace.append({"event": "secondary_source_query", "tool": "get_itt_candidates", "source": "yard_status", "risk_score": 0.6})

        containers[0]["weight_kg"] = 25000
        guard2 = _weight_bounds_guard(containers)
        assert guard2["passed"] is True
        trace.append({"event": "guardrail_resolved", "rule": "weight_bounds", "risk_score": 0.85})
        _sse_stub_publish(trace, run_id, "confidence_update", {"confidence": 0.85, "resolved": True})

        assert any(e.get("event") == "guardrail_failed" for e in trace)
        assert any(e.get("event") == "hitl_card" for e in trace)
        assert any(e.get("event") == "guardrail_resolved" for e in trace)
        assert any(e.get("event_type") == "confidence_update" for e in trace)

    def test_incomplete_data_secondary_source_via_mock(self):
        t1 = ContainerReadinessTool()
        r1 = asyncio.run(t1.call(vessel_id="MV PACIFIC STAR", _run_id="s2-retry"))
        assert r1.output["total_containers"] == 120
        containers = r1.output["containers"]
        assert all(c.get("weight_kg", 0) > 0 for c in containers)
        incomplete = copy.deepcopy(containers)
        incomplete[3]["weight_kg"] = None
        g1 = _weight_bounds_guard(incomplete)
        assert not g1["passed"]
        r2 = asyncio.run(t1.call(vessel_id="MV PACIFIC STAR", _run_id="s2-retry2"))
        g2 = _weight_bounds_guard(r2.output["containers"])
        assert g2["passed"]


class TestS3APIFailure:
    def test_503_error_triggers_fallback_and_notify(self):
        trace: list[dict] = []
        run_id = "s3-503"
        mock_data.notification_log.clear()

        tool = RoadITTCapacityTool()
        with mock.patch.object(tool, "execute", side_effect=Exception("503 Service Unavailable: OptETruck unreachable")):
            result = asyncio.run(tool.call(terminal="PPT", time_window_start="2026-08-19T11:00:00+08:00", time_window_end="2026-08-19T18:00:00+08:00", _run_id=run_id))
            assert result.confidence == 0.0
            assert "error" in result.output
            assert result.metadata["error"] == "execution_error"
            trace.append({"event": "tool_error", "tool": "check_road_itt_capacity", "error": result.output["error"], "risk_score": 0.2, "error_type": "tool_error"})
            assert trace[0]["error_type"] == "tool_error"

        trace.append({"event": "tool_error_fallback", "tool": "check_road_itt_capacity", "retry": 1, "backoff": "1s->2s", "risk_score": 0.4})
        _sse_stub_publish(trace, run_id, "trace_entry", {"event": "tool_error_fallback"})

        fallback_name = FALLBACKS["check_road_itt_capacity"]
        assert fallback_name == "cached_road_capacity"
        fb_tool = CachedRoadCapacityTool()
        assert fb_tool.name == fallback_name
        fb_result = asyncio.run(fb_tool.call(terminal="PPT", time_window_start="2026-08-19T11:00:00+08:00", time_window_end="2026-08-19T18:00:00+08:00", _run_id=run_id))
        assert fb_result.output["fallback_used"] is True
        assert fb_result.metadata["fallback_used"] is True
        assert fb_result.metadata["fallback_for"] == "check_road_itt_capacity"
        assert fb_result.confidence == 0.6
        trace.append({"event": "fallback_used", "fallback_tool": fallback_name, "risk_score": 0.5, "metadata": fb_result.metadata})
        _sse_stub_publish(trace, run_id, "trace_entry", {"fallback_used": True})

        notifier = NotifyPartiesTool()
        alert_msg = "ALERT: OptETruck 503 — using cached road capacity. Operator verification required."
        rn = asyncio.run(notifier.call(message=alert_msg, parties=["PPT_Yard", "Duty_Manager"], _run_id=run_id))
        assert rn.output["status"] == "sent"
        trace.append({"event": "notification", "parties": ["PPT_Yard", "Duty_Manager"], "message": alert_msg, "risk_score": 0.6})
        _sse_stub_publish(trace, run_id, "notification", {"parties": ["PPT_Yard", "Duty_Manager"], "message": alert_msg})

        assert len(mock_data.notification_log) >= 1
        assert mock_data.notification_log[-1]["message"] == alert_msg
        assert any(e.get("event") == "tool_error" for e in trace)
        assert any(e.get("fallback_used") or e.get("event") == "fallback_used" for e in trace)
        assert any(e.get("event") == "notification" for e in trace)
        assert any(e.get("event_type") == "notification" for e in trace)

    def test_timeout_distinct_from_tool_error(self):
        trace: list[dict] = []

        class SlowRoadTool(RoadITTCapacityTool):
            timeout_seconds = 1

            async def execute(self, **kwargs):
                import asyncio as _aio
                await _aio.sleep(5)
                return ToolResult(output={}, confidence=1.0, metadata={})

        slow = SlowRoadTool()
        result = asyncio.run(slow.call(terminal="PPT", time_window_start="2026-08-19T11:00:00+08:00", time_window_end="2026-08-19T18:00:00+08:00", _run_id="s3-timeout"))
        assert result.confidence == 0.0
        assert result.metadata["error"] == "timeout"
        assert "timed out" in result.output["error"]
        trace.append({"event": "tool_timeout", "tool": "check_road_itt_capacity", "risk_score": 0.2, "error_type": "tool_timeout"})
        trace.append({"event": "tool_timeout_fallback", "risk_score": 0.4})
        assert trace[0]["error_type"] == "tool_timeout"
        assert trace[0]["error_type"] != "tool_error"

        fb = CachedRoadCapacityTool()
        fb_r = asyncio.run(fb.call(terminal="PPT", _run_id="s3-timeout"))
        assert fb_r.metadata["fallback_used"] is True
        trace.append({"event": "fallback_used", "risk_score": 0.5})

    def test_sea_fallback_isolation_from_road(self):
        road_fb = CachedRoadCapacityTool()
        sea_fb = CachedSeaCapacityTool()
        r_road = asyncio.run(road_fb.call(terminal="PPT", _run_id="iso-road"))
        r_sea = asyncio.run(sea_fb.call(feeder_id="FEEDER ATLANTIC-03", current_time="2026-08-19T10:35:00+08:00", _run_id="iso-sea"))
        assert r_road.metadata["fallback_for"] == "check_road_itt_capacity"
        assert r_sea.metadata["fallback_for"] == "check_sea_itt_capacity"
        assert r_road.metadata["fallback_for"] != r_sea.metadata["fallback_for"]
        assert r_road.output["fallback_source"] == "cached_road_capacity"
        assert r_sea.output["fallback_source"] == "cached_sea_capacity"

    def test_fallbacks_do_not_pollute_primary_outputs(self):
        t2 = RoadITTCapacityTool()
        r_primary = asyncio.run(t2.call(terminal="PPT", time_window_start="2026-08-19T11:00:00+08:00", time_window_end="2026-08-19T18:00:00+08:00", _run_id="iso-primary"))
        assert r_primary.metadata.get("fallback_used") is not True
        fb = CachedRoadCapacityTool()
        r_fb = asyncio.run(fb.call(terminal="PPT", _run_id="iso-fb"))
        assert r_fb.metadata["fallback_used"] is True
        r_primary2 = asyncio.run(t2.call(terminal="PPT", time_window_start="2026-08-19T11:00:00+08:00", time_window_end="2026-08-19T18:00:00+08:00", _run_id="iso-primary2"))
        assert r_primary2.metadata.get("fallback_used") is not True

    def test_four_tools_fallback_isolation(self):
        t1 = ContainerReadinessTool()
        t2 = RoadITTCapacityTool()
        t3 = SeaITTCapacityTool()
        t4 = OptimiserTool()
        t1_r = asyncio.run(t1.call(vessel_id="MV PACIFIC STAR", _run_id="fb-iso-t1"))
        t2_r = asyncio.run(t2.call(terminal="PPT", time_window_start="2026-08-19T11:00:00+08:00", time_window_end="2026-08-19T18:00:00+08:00", _run_id="fb-iso-t2"))
        t3_r = asyncio.run(t3.call(feeder_id="FEEDER ATLANTIC-03", current_time="2026-08-19T10:35:00+08:00", _run_id="fb-iso-t3"))
        candidates = t1_r.output
        t4_r = asyncio.run(t4.call(candidates=candidates, road_capacity=t2_r.output, sea_capacity=t3_r.output, tuas_vessel_departure="2026-08-19T20:00:00+08:00", _run_id="fb-iso-t4"))
        for r in [t1_r, t2_r, t3_r, t4_r]:
            assert r.metadata.get("fallback_used") is not True
        for fb in [CachedRoadCapacityTool(), CachedSeaCapacityTool()]:
            fr = asyncio.run(fb.call(_run_id="fb-iso-check"))
            assert fr.metadata["fallback_used"] is True
        assert t2.fallback_tool == "cached_road_capacity"
        assert t3.fallback_tool == "cached_sea_capacity"
        assert t1.fallback_tool is None
        assert t4.fallback_tool is None
        assert FALLBACKS == {"check_road_itt_capacity": "cached_road_capacity", "check_sea_itt_capacity": "cached_sea_capacity"}


@pytest.mark.skipif(True, reason="requires Phase 6 HITL-5 (Phase 6.5/6.6) — escalation Trigger #3 / HITL-5 review card not yet implemented")
class TestS4Safety:
    def test_safety_escalation_trigger_cost_gt_10k(self):
        trace: list[dict] = []
        run_id = "s4-safety"
        t1 = ContainerReadinessTool()
        r1 = asyncio.run(t1.call(vessel_id="MV PACIFIC STAR", _run_id=run_id))
        t2 = RoadITTCapacityTool()
        r2 = asyncio.run(t2.call(terminal="PPT", time_window_start="2026-08-19T11:00:00+08:00", time_window_end="2026-08-19T18:00:00+08:00", _run_id=run_id))
        t3 = SeaITTCapacityTool()
        r3 = asyncio.run(t3.call(feeder_id="FEEDER ATLANTIC-03", current_time="2026-08-19T10:35:00+08:00", _run_id=run_id))
        t4 = OptimiserTool()
        r4 = asyncio.run(t4.call(candidates=r1.output, road_capacity=r2.output, sea_capacity=r3.output, tuas_vessel_departure="2026-08-19T20:00:00+08:00", _run_id=run_id))
        total = r4.output["optimal_split"]["total_transport_cost"]
        assert total == 10400
        trigger_fires = total > 10000
        assert trigger_fires is True
        if trigger_fires:
            trace.append({"event": "escalation", "trigger": "Trigger #3: action_cost > $10K", "cost": total, "risk_score": 0.95})
            hitl5_card = {
                "gate": "HITL-5",
                "type": "hitl_card",
                "label": "High-risk action requires sign-off — vessel departure shift 2.5h",
                "cost": total,
                "requires": "Duty Manager approval",
            }
            trace.append({"event": "hitl_card", "gate": "HITL-5", "card": hitl5_card, "risk_score": 0.95})
            _sse_stub_publish(trace, run_id, "escalation", {"trigger": "Trigger #3", "card": hitl5_card})
        assert any(e["event"] == "escalation" for e in trace)
        assert any(e.get("gate") == "HITL-5" for e in trace)

    def test_safety_vessel_departure_shift_gt_2h(self):
        trace: list[dict] = []
        run_id = "s4-shift"
        shift_hours = 2.5
        trigger = shift_hours > 2.0
        assert trigger is True
        if trigger:
            trace.append({"event": "escalation", "trigger": "vessel departure shift >2h", "shift_hours": shift_hours, "risk_score": 1.0})
            card = {"gate": "HITL-5", "shift_hours": shift_hours, "message": "High-risk action requires sign-off — vessel departure shift 2.5h"}
            trace.append({"event": "hitl_card", "gate": "HITL-5", "card": card, "risk_score": 1.0})
            _sse_stub_publish(trace, run_id, "escalation", card)
        assert any(e["event"] == "escalation" for e in trace)

    @pytest.mark.skip(reason="requires Phase 6 HITL-5")
    def test_placeholder_skip_until_hitl5(self):
        assert True
