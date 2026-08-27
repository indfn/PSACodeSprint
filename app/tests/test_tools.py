import asyncio
import pytest

from app.tools.base import BaseTool, ToolResult
from app.tools.registry import ToolRegistry, registry


@pytest.fixture(autouse=True)
def _reset_mocks():
    import app.tools.edge_cases as ec
    ec.reset_edge_cases()
    try:
        import app.mocks.data as d
        d.notification_log.clear()
    except Exception:
        pass
    try:
        from app.mocks import pb01_data as pbd
        pbd.notification_log.clear()
    except Exception:
        pass
    yield
    try:
        import app.tools.edge_cases as ec2
        ec2.reset_edge_cases()
    except Exception:
        pass


class TestContainerReadiness:
    @pytest.mark.asyncio
    async def test_get_itt_candidates_returns_120(self):
        from app.tools.container_readiness import ContainerReadinessTool
        tool = ContainerReadinessTool()
        r = await tool.call(vessel_id="MV PACIFIC STAR", _run_id="run-t1")
        assert isinstance(r, ToolResult)
        assert r.output["total_containers"] == 120
        assert r.output["total_teu"] == 160
        assert r.output["dg_containers"] == 3
        assert r.output["blocks_affected"] == ["B-07", "B-08", "B-12", "B-14"]
        assert r.output["lta_truck_trip_requirement"]["total_potential_truck_trips_100pct_road"] == 80
        assert r.confidence == 0.95
        assert r.output["container_breakdown"]["40ft_feu"] == 40
        assert r.output["container_breakdown"]["20ft_teu"] == 80

    @pytest.mark.asyncio
    async def test_via_registry(self):
        registry.register_for_problem("pb-12-itt")
        r = await registry.call("get_itt_candidates", vessel_id="MV PACIFIC STAR", _run_id="run-reg")
        assert r.output["total_containers"] == 120
        assert r.confidence > 0


class TestRoadITTCapacity:
    @pytest.mark.asyncio
    async def test_offpeak_vs_peak_transit_differs(self):
        from app.tools.road_itt import RoadITTCapacityTool
        tool = RoadITTCapacityTool()
        off = await tool.call(terminal="PPT", time_window_start="2026-08-19T10:00:00+08:00", time_window_end="2026-08-19T12:00:00+08:00", _run_id="r-off")
        peak = await tool.call(terminal="PPT", time_window_start="2026-08-19T08:00:00+08:00", time_window_end="2026-08-19T10:00:00+08:00", _run_id="r-peak")
        assert off.output["transit_time_minutes"] == 90
        assert peak.output["transit_time_minutes"] == 110
        assert off.output["transit_time_minutes"] != peak.output["transit_time_minutes"]
        assert off.confidence == 0.95
        assert peak.confidence == 0.7

    @pytest.mark.asyncio
    async def test_fleet_varies_by_time_window(self):
        from app.tools.road_itt import RoadITTCapacityTool
        tool = RoadITTCapacityTool()
        r06 = await tool.call(terminal="PPT", time_window_start="2026-08-19T06:30:00+08:00", time_window_end="2026-08-19T08:30:00+08:00", _run_id="r06")
        r09 = await tool.call(terminal="PPT", time_window_start="2026-08-19T09:30:00+08:00", time_window_end="2026-08-19T11:30:00+08:00", _run_id="r09")
        r13 = await tool.call(terminal="PPT", time_window_start="2026-08-19T13:00:00+08:00", time_window_end="2026-08-19T15:00:00+08:00", _run_id="r13")
        assert r06.output["available_trucks"] == 18
        assert r09.output["available_trucks"] == 20
        assert r13.output["available_trucks"] == 22
        assert len({r06.output["available_trucks"], r09.output["available_trucks"], r13.output["available_trucks"]}) > 1

    @pytest.mark.asyncio
    async def test_esc_5_flag_when_available_below_threshold(self):
        from app.tools.road_itt import RoadITTCapacityTool
        tool = RoadITTCapacityTool()
        r = await tool.call(terminal="PPT", time_window_start="2026-08-19T10:00:00+08:00", time_window_end="2026-08-19T12:00:00+08:00", _run_id="r-esc")
        assert r.output["esc_5_flag"] is True
        assert "esc_5" in r.output
        assert r.output["esc_5"]["trigger_id"] == "esc_5"
        assert r.output["capacity_ratio"] == pytest.approx(20 / 80, rel=0.01)

    @pytest.mark.asyncio
    async def test_via_registry(self):
        registry.register_for_problem("pb-12-itt")
        r = await registry.call("check_road_itt_capacity", terminal="PPT", time_window_start="2026-08-19T10:00:00+08:00", time_window_end="2026-08-19T12:00:00+08:00", _run_id="r-reg")
        assert r.output["status"] == "success"
        assert r.output["transit_time_minutes"] in (90, 110)


class TestSeaITTCapacity:
    @pytest.mark.asyncio
    async def test_atlantic_03_returns_window_downstream(self):
        from app.tools.sea_itt import SeaITTCapacityTool
        tool = SeaITTCapacityTool()
        r = await tool.call(feeder_id="FEEDER ATLANTIC-03", current_time="2026-08-19T10:00:00+08:00", _run_id="s1")
        out = r.output
        assert out["capacity_teu"] == 800
        assert out["available_capacity_teu"] == 180
        assert out["available"] == 180
        assert out["berth_status"] == "berthed_at_PPT_B12"
        assert "departure_window" in out
        assert set(["earliest", "latest", "requested"]).issubset(out["departure_window"].keys())
        assert out["downstream_constraints"]["destination_port"] == "Port Klang"
        assert out["downstream_constraints"]["tidal_window"] == "2026-08-19T23:00:00+08:00"
        assert out["downstream"]["destination_port"] == "Port Klang"
        assert out["hold_cost_per_hour"] == 800
        assert out["missed_connection_cost"] == 5000
        assert out["capacity"]["available_capacity_teu"] == 180

    @pytest.mark.asyncio
    async def test_hold_cost_scenarios(self):
        from app.tools.sea_itt import SeaITTCapacityTool
        tool = SeaITTCapacityTool()
        r = await tool.call(feeder_id="FEEDER ATLANTIC-03", current_time="2026-08-19T10:00:00+08:00", _run_id="s2")
        scenarios = r.output.get("hold_cost_scenarios") or r.output.get("hold_cost")
        assert scenarios is not None
        assert "1h" in scenarios and "2h" in scenarios and "3h" in scenarios and "6h" in scenarios
        assert scenarios["1h"]["hold_cost"] == 800
        assert scenarios["2h"]["hold_cost"] == 1600
        assert scenarios["6h"]["hold_cost"] == 4800

    @pytest.mark.asyncio
    async def test_downstream_tidal_and_berth_status(self):
        from app.tools.sea_itt import SeaITTCapacityTool
        tool = SeaITTCapacityTool()
        r = await tool.call(feeder_id="FEEDER ATLANTIC-03", current_time="2026-08-19T10:00:00+08:00", _run_id="s3")
        assert r.output["downstream_constraints"]["must_depart_by"] == "2026-08-19T05:00:00+08:00"
        assert r.output["berth_status"] != ""
        assert r.output["is_berthed"] is True
        assert r.output["tidal_risk"] in ("safe", "marginal", "critical")
        assert r.output["latest_safe_departure"] is not None


class TestOptimiser:
    @pytest.mark.asyncio
    async def test_80_40_split_10400(self):
        from app.tools.optimiser import OptimiserTool
        from app.mocks.data import get_container_data, get_truck_data, get_feeder_data
        tool = OptimiserTool()
        r = await tool.call(candidates=get_container_data(), road_capacity=get_truck_data(), sea_capacity=get_feeder_data(), tuas_vessel_departure="2026-08-19T20:00:00+08:00", _run_id="opt-1")
        opt = r.output["optimal_split"]
        assert opt["road_containers"] == 80
        assert opt["sea_containers"] == 40
        assert opt["total_transport_cost"] == 10400
        assert opt["road_trips"] == 60
        assert opt["road_cost"] == 9000
        assert opt["sea_terminal_handling_cost"] == 1400

    @pytest.mark.asyncio
    async def test_alternatives_present(self):
        from app.tools.optimiser import OptimiserTool
        from app.mocks.data import get_container_data, get_truck_data, get_feeder_data
        tool = OptimiserTool()
        r = await tool.call(candidates=get_container_data(), road_capacity=get_truck_data(), sea_capacity=get_feeder_data(), tuas_vessel_departure="2026-08-19T20:00:00+08:00", _run_id="opt-alt")
        alts = r.output["alternatives"]
        assert len(alts) >= 2
        assert any(a["road_containers"] == 100 and a["sea_containers"] == 20 for a in alts)
        assert any(a["road_containers"] == 60 and a["sea_containers"] == 60 for a in alts)
        for a in alts:
            assert "total_transport_cost" in a

    @pytest.mark.asyncio
    async def test_guardrails(self):
        from app.tools.optimiser import OptimiserTool
        from app.mocks.data import get_container_data, get_truck_data, get_feeder_data
        tool = OptimiserTool()
        r = await tool.call(candidates=get_container_data(), road_capacity=get_truck_data(), sea_capacity=get_feeder_data(), tuas_vessel_departure="2026-08-19T20:00:00+08:00", _run_id="opt-guard")
        g = r.output["guardrails_checked"]
        assert "containers_per_block_le_max" in g
        assert "sea_containers_le_feeder_available" in g
        assert "itt_arrival_lt_vessel_minus_60" in g
        assert "feeder_departure_lt_tidal_deadline" in g
        assert all(v["passed"] is True for v in g.values())
        assert r.output["constraints_validated"]["all_guardrails_passed"] is True

    @pytest.mark.asyncio
    async def test_timeline_and_cost_vs_baseline(self):
        from app.tools.optimiser import OptimiserTool
        from app.mocks.data import get_container_data, get_truck_data, get_feeder_data
        tool = OptimiserTool()
        r = await tool.call(candidates=get_container_data(), road_capacity=get_truck_data(), sea_capacity=get_feeder_data(), tuas_vessel_departure="2026-08-19T20:00:00+08:00", _run_id="opt-tl")
        tl = r.output["timeline"]
        assert tl["road_itt_arrival"] == "2026-08-19T14:30:00+08:00"
        assert tl["sea_itt_arrival"] == "2026-08-19T16:30:00+08:00"
        assert tl["vessel_departure"] == "2026-08-19T20:00:00+08:00"
        cvb = r.output["cost_vs_baseline"]
        assert cvb["baseline_all_road"] == 12000
        assert cvb["optimised"] == 10400
        assert cvb["savings"] == 1600
        assert r.output["roi"]["per_incident"] == 8000


class TestTuasLoading:
    @pytest.mark.asyncio
    async def test_qc_adjustments_map_80_40(self):
        from app.tools.tuas_loading import TuasLoadingTool
        from app.mocks.data import generate_containers
        tool = TuasLoadingTool()
        containers = generate_containers()
        ids_road = [c["container_id"] for c in containers[:80]]
        ids_sea = [c["container_id"] for c in containers[80:]]
        r = await tool.call(vessel_id="MV PACIFIC STAR", itt_eta_road="2026-08-19T14:30:00+08:00", itt_eta_sea="2026-08-19T16:30:00+08:00", container_ids_road=ids_road, container_ids_sea=ids_sea, _run_id="tuas-1")
        out = r.output
        assert out["road_container_count"] == 80
        assert out["sea_container_count"] == 40
        assert out["total_itt_containers"] == 120
        assert len(out["qc_adjustments"]) == 4
        etas = [a["eta"] for a in out["qc_adjustments"]]
        assert "2026-08-19T14:30:00+08:00" in etas
        assert "2026-08-19T16:30:00+08:00" in etas

    @pytest.mark.asyncio
    async def test_etas_passed_through(self):
        from app.tools.tuas_loading import TuasLoadingTool
        from app.mocks.data import generate_containers
        tool = TuasLoadingTool()
        containers = generate_containers()
        ids_road = [c["container_id"] for c in containers[:80]]
        ids_sea = [c["container_id"] for c in containers[80:]]
        r = await tool.call(vessel_id="MV PACIFIC STAR", itt_eta_road="2026-08-19T14:30:00+08:00", itt_eta_sea="2026-08-19T16:30:00+08:00", container_ids_road=ids_road, container_ids_sea=ids_sea, _run_id="tuas-2")
        assert "2026-08-19T14:30:00+08:00" in r.output["updated_loading_sequence"]
        assert "2026-08-19T16:30:00+08:00" in r.output["updated_loading_sequence"]
        assert r.output["estimated_loading_completion"] == "2026-08-19T19:30:00+08:00"
        assert r.output["margin_before_departure_minutes"] == 30


class TestDispatchRoadITT:
    @pytest.mark.asyncio
    async def test_dispatch_confirmation(self):
        from app.tools.dispatch_road_itt import DispatchRoadITTTool
        from app.mocks.data import generate_containers
        tool = DispatchRoadITTTool()
        containers = generate_containers()
        ids = [c["container_id"] for c in containers[:10]]
        r = await tool.call(num_trucks=4, route="PPT → West Coast Highway → AYE → Tuas Port Boulevard", container_ids=ids, _run_id="disp-1")
        assert r.output["status"] == "dispatched"
        assert r.output["num_trucks"] == 4
        assert r.output["container_ids"] == ids
        assert r.output["container_count"] == 10
        assert "dispatch_id" in r.output
        assert r.output["eta"] == "2026-08-19T14:30:00+08:00"

    @pytest.mark.asyncio
    async def test_delta_dispatch(self):
        from app.tools.dispatch_road_itt import DispatchRoadITTTool
        from app.mocks.data import generate_containers
        tool = DispatchRoadITTTool()
        containers = generate_containers()
        ids = [c["container_id"] for c in containers[:20]]
        r = await tool.call(num_trucks=4, route="PPT → West Coast Highway → AYE → Tuas Port Boulevard", container_ids=ids, _run_id="disp-delta")
        assert r.output["num_trucks"] == 4
        assert isinstance(r.output["container_ids"], list)
        assert len(r.output["truck_assignments"]) == 4
        assert r.confidence == 0.95
        assert tool.post_approval is True

    @pytest.mark.asyncio
    async def test_hitl_guard_note(self):
        from app.tools.dispatch_road_itt import DispatchRoadITTTool
        tool = DispatchRoadITTTool()
        assert tool.post_approval is True
        assert "HITL" in tool.description


class TestRequestFeederHold:
    @pytest.mark.asyncio
    async def test_hold_confirmation_cost(self):
        from app.tools.request_feeder_hold import RequestFeederHoldTool
        tool = RequestFeederHoldTool()
        r = await tool.call(feeder_id="FEEDER ATLANTIC-03", hold_hours=2, _run_id="hold-1")
        assert r.output["status"] == "accepted"
        assert r.output["hold_cost"] == 1600.0
        assert r.output["hold_cost_per_hour"] == 800.0
        assert r.output["hold_hours"] == 2.0
        assert r.output["operator_response"] == "accepted"

    @pytest.mark.asyncio
    async def test_operator_decline_hold_gt4(self):
        from app.tools.request_feeder_hold import RequestFeederHoldTool
        tool = RequestFeederHoldTool()
        r = await tool.call(feeder_id="FEEDER ATLANTIC-03", hold_hours=5, _run_id="hold-decline")
        assert r.output["status"] == "declined"
        assert r.output["operator_response"] == "declined"
        assert r.output["hold_cost"] == 4000.0
        assert r.confidence == 0.5

    @pytest.mark.asyncio
    async def test_operator_decline_feeder_id(self):
        from app.tools.request_feeder_hold import RequestFeederHoldTool
        tool = RequestFeederHoldTool()
        r = await tool.call(feeder_id="FEEDER DECLINE-01", hold_hours=2, _run_id="hold-decline2")
        assert r.output["status"] == "declined"
        assert r.output["operator_response"] == "declined"

    @pytest.mark.asyncio
    async def test_hold_cost_one_hour(self):
        from app.tools.request_feeder_hold import RequestFeederHoldTool
        tool = RequestFeederHoldTool()
        r = await tool.call(feeder_id="FEEDER ATLANTIC-03", hold_hours=1, _run_id="hold-1h")
        assert r.output["hold_cost"] == 800.0


class TestNotifyParties:
    @pytest.mark.asyncio
    async def test_notify_trace_and_log(self):
        from app.tools.notify import NotifyPartiesTool
        import app.mocks.data as d
        d.notification_log.clear()
        tool = NotifyPartiesTool()
        r = await tool.call(message="Feeder delayed to 1600", parties=["PPT_Yard", "Tuas_Yard"], _run_id="notify-1")
        assert r.output["notified"] == ["PPT_Yard", "Tuas_Yard"]
        assert r.output["message"] == "Feeder delayed to 1600"
        assert r.output["status"] == "sent"
        assert r.output["trace_hint"]["event"] == "notification"
        assert r.metadata["notification"]["event"] == "notification"
        assert len(d.notification_log) == 1
        assert d.notification_log[0]["message"] == "Feeder delayed to 1600"
        assert d.notification_log[0]["parties"] == ["PPT_Yard", "Tuas_Yard"]
        assert r.confidence == 1.0

    @pytest.mark.asyncio
    async def test_sse_graceful_fallback(self):
        from app.tools.notify import NotifyPartiesTool
        import app.mocks.data as d
        d.notification_log.clear()
        tool = NotifyPartiesTool()
        r = await tool.call(message="Test SSE fallback", parties=["PPT_Yard"], _run_id="notify-sse")
        assert r.output["status"] == "sent"
        assert len(d.notification_log) == 1


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_inject_feeder_berth_conflict(self):
        import app.tools.edge_cases as ec
        from app.mocks.data import get_feeder_data
        from app.tools.sea_itt import SeaITTCapacityTool
        ec.inject_feeder_berth_conflict(feeder_id="FEEDER ATLANTIC-03", new_departure="2026-08-19T16:00:00+08:00")
        data = get_feeder_data(feeder_id="FEEDER ATLANTIC-03")
        assert data["berth_status"] == "conflict"
        assert data["departure_window"]["latest"] == "2026-08-19T16:00:00+08:00"
        tool = SeaITTCapacityTool()
        r = await tool.call(feeder_id="FEEDER ATLANTIC-03", current_time="2026-08-19T10:00:00+08:00", _run_id="edge-1")
        assert "conflict" in str(r.output["berth_status"]).lower()

    @pytest.mark.asyncio
    async def test_inject_stale_data(self):
        import app.tools.edge_cases as ec
        from app.mocks.data import get_container_data
        from app.tools.container_readiness import ContainerReadinessTool
        ec.inject_stale_data(time_offset_minutes=25)
        data = get_container_data()
        assert data["data_age_minutes"] == 25.0
        assert data["edge_case"] == "data_staleness"
        tool = ContainerReadinessTool()
        r = await tool.call(vessel_id="MV PACIFIC STAR", _run_id="edge-2")
        assert r.output["data_age_minutes"] == 25.0
        assert r.confidence == 0.8

    @pytest.mark.asyncio
    async def test_reset_restores(self):
        import app.tools.edge_cases as ec
        from app.mocks.data import get_feeder_data, get_container_data
        ec.inject_feeder_berth_conflict()
        ec.inject_stale_data(30)
        ec.reset_edge_cases()
        assert get_feeder_data()["berth_status"] == "berthed_at_PPT_B12"
        assert get_container_data()["data_age_minutes"] == 0.5
        assert "edge_case" not in get_container_data() or get_container_data().get("edge_case") != "data_staleness"


class TestToolRegistryIntegration:
    @pytest.mark.asyncio
    async def test_register_all_pb12_tools(self):
        registry.register_for_problem("pb-12-itt")
        tools = registry.list()
        assert len(tools) == 8
        assert set(tools) == {"get_itt_candidates", "check_road_itt_capacity", "check_sea_itt_capacity", "compute_itt_split", "update_tuas_loading_sequence", "dispatch_road_itt", "request_feeder_hold", "notify_parties"}

    @pytest.mark.asyncio
    async def test_get_schemas_8(self):
        registry.register_for_problem("pb-12-itt")
        schemas = registry.get_schemas()
        assert len(schemas) == 8
        names = {s["name"] for s in schemas}
        assert names == set(registry.list())
        for s in schemas:
            assert "name" in s and "description" in s and "parameters" in s

    @pytest.mark.asyncio
    async def test_call_each_via_registry(self):
        from app.mocks.data import generate_containers, get_container_data, get_truck_data, get_feeder_data
        registry.register_for_problem("pb-12-itt")
        containers = generate_containers()
        ids_road = [c["container_id"] for c in containers[:80]]
        ids_sea = [c["container_id"] for c in containers[80:]]

        r1 = await registry.call("get_itt_candidates", vessel_id="MV PACIFIC STAR", _run_id="reg-t1")
        assert r1.output["total_containers"] == 120

        r2 = await registry.call("check_road_itt_capacity", terminal="PPT", time_window_start="2026-08-19T10:00:00+08:00", time_window_end="2026-08-19T12:00:00+08:00", _run_id="reg-t2")
        assert r2.output["status"] == "success"

        r3 = await registry.call("check_sea_itt_capacity", feeder_id="FEEDER ATLANTIC-03", current_time="2026-08-19T10:00:00+08:00", _run_id="reg-t3")
        assert r3.output["status"] == "success"

        r4 = await registry.call("compute_itt_split", candidates=get_container_data(), road_capacity=get_truck_data(), sea_capacity=get_feeder_data(), tuas_vessel_departure="2026-08-19T20:00:00+08:00", _run_id="reg-t4")
        assert r4.output["optimal_split"]["total_transport_cost"] == 10400

        r5 = await registry.call("update_tuas_loading_sequence", vessel_id="MV PACIFIC STAR", itt_eta_road="2026-08-19T14:30:00+08:00", itt_eta_sea="2026-08-19T16:30:00+08:00", container_ids_road=ids_road, container_ids_sea=ids_sea, _run_id="reg-t5")
        assert r5.output["status"] == "success"

        r6 = await registry.call("dispatch_road_itt", num_trucks=4, route="PPT → West Coast Highway → AYE → Tuas Port Boulevard", container_ids=ids_road[:10], _run_id="reg-t6")
        assert r6.output["status"] == "dispatched"

        r7 = await registry.call("request_feeder_hold", feeder_id="FEEDER ATLANTIC-03", hold_hours=1, _run_id="reg-t7")
        assert r7.output["hold_cost"] == 800.0

        r8 = await registry.call("notify_parties", message="hello", parties=["PPT_Yard"], _run_id="reg-t8")
        assert r8.output["status"] == "sent"

    @pytest.mark.asyncio
    async def test_error_handling_missing_params(self):
        from app.tools.container_readiness import ContainerReadinessTool
        tool = ContainerReadinessTool()
        r = await tool.call(_run_id="err-missing")
        assert r.confidence == 0.0
        assert "error" in r.output
        assert r.metadata["error"] == "missing_required:vessel_id"

    @pytest.mark.asyncio
    async def test_error_handling_hallucinated_tool(self):
        r = await registry.call("hallucinated_tool_xyz", _run_id="err-hall")
        assert r.confidence == 0.0
        assert "Unknown tool" in r.output["error"]
        assert r.metadata["error"] == "hallucinated"

    @pytest.mark.asyncio
    async def test_error_handling_hallucinated_arg(self):
        from app.tools.container_readiness import ContainerReadinessTool
        tool = ContainerReadinessTool()
        r = await tool.call(vessel_id="MV X", hallucinated_param="oops", _run_id="err-arg")
        assert r.confidence == 0.0
        assert "error" in r.output


class TestToolResultFormat:
    @pytest.mark.asyncio
    async def test_each_tool_returns_valid_toolresult(self):
        from app.mocks.data import generate_containers, get_container_data, get_truck_data, get_feeder_data
        from app.tools.container_readiness import ContainerReadinessTool
        from app.tools.road_itt import RoadITTCapacityTool
        from app.tools.sea_itt import SeaITTCapacityTool
        from app.tools.optimiser import OptimiserTool
        from app.tools.tuas_loading import TuasLoadingTool
        from app.tools.dispatch_road_itt import DispatchRoadITTTool
        from app.tools.request_feeder_hold import RequestFeederHoldTool
        from app.tools.notify import NotifyPartiesTool

        containers = generate_containers()
        ids_road = [c["container_id"] for c in containers[:80]]
        ids_sea = [c["container_id"] for c in containers[80:]]

        cases = [
            (ContainerReadinessTool(), dict(vessel_id="MV PACIFIC STAR")),
            (RoadITTCapacityTool(), dict(terminal="PPT", time_window_start="2026-08-19T10:00:00+08:00", time_window_end="2026-08-19T12:00:00+08:00")),
            (SeaITTCapacityTool(), dict(feeder_id="FEEDER ATLANTIC-03", current_time="2026-08-19T10:00:00+08:00")),
            (OptimiserTool(), dict(candidates=get_container_data(), road_capacity=get_truck_data(), sea_capacity=get_feeder_data(), tuas_vessel_departure="2026-08-19T20:00:00+08:00")),
            (TuasLoadingTool(), dict(vessel_id="MV PACIFIC STAR", itt_eta_road="2026-08-19T14:30:00+08:00", itt_eta_sea="2026-08-19T16:30:00+08:00", container_ids_road=ids_road, container_ids_sea=ids_sea)),
            (DispatchRoadITTTool(), dict(num_trucks=4, route="PPT → West Coast Highway → AYE → Tuas Port Boulevard", container_ids=ids_road[:10])),
            (RequestFeederHoldTool(), dict(feeder_id="FEEDER ATLANTIC-03", hold_hours=1)),
            (NotifyPartiesTool(), dict(message="test", parties=["PPT_Yard"])),
        ]
        for tool, kwargs in cases:
            r = await tool.call(**kwargs, _run_id=f"fmt-{tool.name}")
            assert isinstance(r, ToolResult), f"{tool.name} not ToolResult"
            assert isinstance(r.output, dict), f"{tool.name} output not dict"
            assert 0.0 <= r.confidence <= 1.0, f"{tool.name} confidence out of range {r.confidence}"
            assert "tool_name" in r.metadata
            assert r.metadata["tool_name"] == tool.name
            assert "timestamp" in r.metadata
            assert "duration_ms" in r.metadata
            assert isinstance(r.metadata["duration_ms"], int)
            assert "run_id" in r.metadata
            assert r.metadata["run_id"] == f"fmt-{tool.name}"
            assert "T" in r.metadata["timestamp"]

    @pytest.mark.asyncio
    async def test_confidence_valid_range(self):
        from app.tools.container_readiness import ContainerReadinessTool
        tool = ContainerReadinessTool()
        r_ok = await tool.call(vessel_id="MV PACIFIC STAR", _run_id="conf-ok")
        assert 0 <= r_ok.confidence <= 1
        r_err = await tool.call(_run_id="conf-err")
        assert r_err.confidence == 0.0


class TestPB01Switch:
    @pytest.mark.asyncio
    async def test_switch_to_pb01_and_back(self):
        registry.register_for_problem("pb-01-berth")
        tools01 = set(registry.list())
        assert len(tools01) == 5
        assert tools01 == {"query_vessel_arrival", "check_berth_availability", "check_qc_availability", "compute_berth_reassignment", "notify_vessel_operator"}
        schemas = registry.get_schemas()
        assert len(schemas) == 5

        r1 = await registry.call("query_vessel_arrival", vessel_id="MV EVER GIVEN", _run_id="pb01-1")
        assert isinstance(r1, ToolResult)
        assert 0 <= r1.confidence <= 1
        assert r1.output["vessel_id"] == "MV EVER GIVEN"

        r2 = await registry.call("check_berth_availability", berth_id="B-03", _run_id="pb01-2")
        assert isinstance(r2, ToolResult)
        assert r2.output["berth_id"] == "B-03"

        r3 = await registry.call("check_qc_availability", berth_id="B-03", _run_id="pb01-3")
        assert isinstance(r3, ToolResult)
        assert r3.output["berth_id"] == "B-03"

        r4 = await registry.call("compute_berth_reassignment", vessel_id="MV EVER GIVEN", _run_id="pb01-4")
        assert isinstance(r4, ToolResult)
        assert r4.output["status"] == "computed"

        r5 = await registry.call("notify_vessel_operator", vessel_id="MV EVER GIVEN", message="hello", _run_id="pb01-5")
        assert isinstance(r5, ToolResult)
        assert r5.output["status"] == "sent"

        registry.register_for_problem("pb-12-itt")
        tools12 = set(registry.list())
        assert len(tools12) == 8
        assert "get_itt_candidates" in tools12
        assert "check_road_itt_capacity" in tools12

    @pytest.mark.asyncio
    async def test_pb01_tools_valid_toolresult_via_direct_call(self):
        from app.tools.pb01.query_vessel_arrival import QueryVesselArrivalTool
        from app.tools.pb01.check_berth_availability import CheckBerthAvailabilityTool
        from app.tools.pb01.check_qc_availability import CheckQCAvailabilityTool
        from app.tools.pb01.compute_berth_reassignment import ComputeBerthReassignmentTool
        from app.tools.pb01.notify_vessel_operator import NotifyVesselOperatorTool
        for tool, kwargs in [
            (QueryVesselArrivalTool(), dict(vessel_id="MV EVER GIVEN")),
            (CheckBerthAvailabilityTool(), dict(berth_id="B-03")),
            (CheckQCAvailabilityTool(), dict(berth_id="B-03")),
            (ComputeBerthReassignmentTool(), dict(vessel_id="MV EVER GIVEN")),
            (NotifyVesselOperatorTool(), dict(vessel_id="MV EVER GIVEN", message="test")),
        ]:
            r = await tool.call(**kwargs, _run_id=f"pb01-direct-{tool.name}")
            assert isinstance(r, ToolResult)
            assert 0 <= r.confidence <= 1
            assert "tool_name" in r.metadata
