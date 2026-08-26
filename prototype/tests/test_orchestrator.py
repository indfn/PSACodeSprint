"""Tests for pre_approval.orchestrator — pre-approval ITT pipeline."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from prototype.pre_approval.orchestrator import (
    PreApprovalResult,
    _validate_and_bootstrap,
    _gather_t1,
    _gather_t2,
    _gather_t3,
    _gather_parallel,
    _run_optimisation,
    run_pre_approval_pipeline,
)
from prototype.pre_approval.container_readiness.webhook import ITTCoordinationEvent

SGT = timezone(timedelta(hours=8))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_valid_event(**overrides) -> ITTCoordinationEvent:
    """Build a valid ITTCoordinationEvent with sensible defaults."""
    defaults = {
        "event_type": "ITT_COORDINATION_REQUEST",
        "timestamp": "2026-08-19T10:30:00+08:00",
        "source": "CITOS_PPT",
        "priority": "high",
        "origin_terminal": "PPT",
        "destination_terminal": "TUAS",
        "vessel_id": "MV PACIFIC STAR",
        "tuas_vessel_departure": (datetime.now(SGT) + timedelta(hours=6)).isoformat(),
        "container_count": 120,
        "containers_ready": 120,
        "blocks_affected": ["B-07", "B-08", "B-12", "B-14"],
        "dg_containers": 3,
        "priority_containers": 45,
        "requested_by": "PPT_Yard_Planner_Lim",
        "notes": "Test",
    }
    defaults.update(overrides)
    return ITTCoordinationEvent(**defaults)


@pytest.fixture
def valid_event():
    return _make_valid_event()


@pytest.fixture
def mock_candidates():
    return {
        "status": "success",
        "vessel_id": "MV PACIFIC STAR",
        "total_containers": 120,
        "container_breakdown": {"40ft_feu": 40, "20ft_teu": 80},
        "containers": [{"container_id": "MSKU1000000", "size": "40ft"}],
    }


@pytest.fixture
def mock_road_capacity():
    return {
        "status": "success",
        "available_trucks": 20,
        "transit_time_minutes": 45,
        "cost_per_trip": 150,
    }


@pytest.fixture
def mock_sea_capacity():
    return {
        "status": "success",
        "available_capacity_teu": 180,
        "departure_window": {
            "earliest": "2026-08-19T14:00:00+08:00",
            "latest": "2026-08-19T16:00:00+08:00",
        },
    }


@pytest.fixture
def mock_split_result():
    return {
        "status": "success",
        "optimal_split": {
            "road_containers": 80,
            "sea_containers": 40,
            "total_transport_cost": 7500,
        },
        "confidence": 0.92,
        "escalation_flags": [],
    }


# ---------------------------------------------------------------------------
# PreApprovalResult
# ---------------------------------------------------------------------------

class TestPreApprovalResult:
    def test_init(self, valid_event):
        result = PreApprovalResult(
            run_id="run-abc123",
            event=valid_event.model_dump(),
            agent_state={"key": "val"},
            split_result={"optimal_split": {"road_containers": 80}},
        )
        assert result.run_id == "run-abc123"
        assert result.event["vessel_id"] == "MV PACIFIC STAR"
        assert result.agent_state == {"key": "val"}
        assert result.split_result["optimal_split"]["road_containers"] == 80

    def test_to_dict(self, valid_event):
        result = PreApprovalResult(
            run_id="run-xyz",
            event=valid_event.model_dump(),
            agent_state={"a": 1},
            split_result={"b": 2},
        )
        d = result.to_dict()
        assert d["run_id"] == "run-xyz"
        assert d["event"]["vessel_id"] == "MV PACIFIC STAR"
        assert d["agent_state"] == {"a": 1}
        assert d["split_result"] == {"b": 2}
        assert isinstance(d, dict)


# ---------------------------------------------------------------------------
# _validate_and_bootstrap
# ---------------------------------------------------------------------------

class TestValidateAndBootstrap:
    def test_valid_event(self, valid_event):
        state, run_id = _validate_and_bootstrap(valid_event)
        assert run_id.startswith("run-")
        assert len(run_id) == 16  # "run-" + 12 hex chars
        assert state["vessel_id"] == "MV PACIFIC STAR"
        assert state["container_count"] == 120
        assert state["origin_terminal"] == "PPT"
        assert state["destination_terminal"] == "TUAS"
        assert state["current_step"] == "ingest"
        assert state["hitl_pending"] == []
        assert state["escalations"] == []

    def test_low_container_count_raises(self):
        event = _make_valid_event(container_count=10, containers_ready=10)
        with pytest.raises(ValueError, match="Webhook validation failed"):
            _validate_and_bootstrap(event)

    def test_past_departure_raises(self):
        event = _make_valid_event(
            tuas_vessel_departure=(datetime.now(SGT) - timedelta(hours=1)).isoformat()
        )
        with pytest.raises(ValueError, match="Webhook validation failed"):
            _validate_and_bootstrap(event)

    def test_containers_ready_exceeds_count_raises(self):
        event = _make_valid_event(container_count=120, containers_ready=150)
        with pytest.raises(ValueError, match="Webhook validation failed"):
            _validate_and_bootstrap(event)

    def test_run_id_is_unique(self, valid_event):
        _, run_id1 = _validate_and_bootstrap(valid_event)
        _, run_id2 = _validate_and_bootstrap(valid_event)
        assert run_id1 != run_id2


# ---------------------------------------------------------------------------
# _gather_t1 / _gather_t2 / _gather_t3
# ---------------------------------------------------------------------------

class TestGatherT1:
    @patch("prototype.pre_approval.orchestrator.get_itt_candidates")
    def test_calls_with_vessel_id(self, mock_get):
        mock_get.return_value = {
            "total_containers": 120,
            "container_breakdown": {"40ft_feu": 40, "20ft_teu": 80},
        }
        state = {"vessel_id": "MV PACIFIC STAR"}
        result = _gather_t1(state)
        mock_get.assert_called_once_with(vessel_id="MV PACIFIC STAR")
        assert result["total_containers"] == 120

    @patch("prototype.pre_approval.orchestrator.get_itt_candidates")
    def test_returns_full_result(self, mock_get):
        mock_get.return_value = {"total_containers": 50, "container_breakdown": {"40ft_feu": 20, "20ft_teu": 30}}
        state = {"vessel_id": "TEST VESSEL"}
        result = _gather_t1(state)
        assert result == {"total_containers": 50, "container_breakdown": {"40ft_feu": 20, "20ft_teu": 30}}


class TestGatherT2:
    @patch("prototype.pre_approval.orchestrator.check_road_itt_capacity")
    def test_calls_with_correct_params(self, mock_check):
        mock_check.return_value = {"available_trucks": 20}
        state = {
            "origin_terminal": "PPT",
            "tuas_vessel_departure": "2026-08-19T20:00:00+08:00",
        }
        result = _gather_t2(state)
        assert mock_check.called
        call_kwargs = mock_check.call_args
        assert call_kwargs[1]["terminal"] == "PPT" or call_kwargs[0][1] == "PPT"
        assert result["available_trucks"] == 20

    @patch("prototype.pre_approval.orchestrator.check_road_itt_capacity")
    def test_handles_naive_departure(self, mock_check):
        mock_check.return_value = {"transit_time_minutes": 45}
        state = {
            "origin_terminal": "PPT",
            "tuas_vessel_departure": "2026-08-19T20:00:00",
        }
        result = _gather_t2(state)
        assert result["transit_time_minutes"] == 45


class TestGatherT3:
    @patch("prototype.pre_approval.orchestrator.check_sea_itt_capacity")
    def test_calls_with_correct_params(self, mock_check):
        mock_check.return_value = {"available_capacity_teu": 180}
        state = {}
        result = _gather_t3(state)
        mock_check.assert_called_once()
        assert result["available_capacity_teu"] == 180


# ---------------------------------------------------------------------------
# _gather_parallel
# ---------------------------------------------------------------------------

class TestGatherParallel:
    @pytest.mark.asyncio
    @patch("prototype.pre_approval.orchestrator._gather_t3", return_value={"sea": True})
    @patch("prototype.pre_approval.orchestrator._gather_t2", return_value={"road": True})
    @patch("prototype.pre_approval.orchestrator._gather_t1", return_value={"cand": True})
    async def test_runs_all_three_concurrently(self, mock_t1, mock_t2, mock_t3):
        state = {"vessel_id": "MV TEST"}
        candidates, road, sea = await _gather_parallel(state)
        assert candidates == {"cand": True}
        assert road == {"road": True}
        assert sea == {"sea": True}
        mock_t1.assert_called_once()
        mock_t2.assert_called_once()
        mock_t3.assert_called_once()


# ---------------------------------------------------------------------------
# _run_optimisation
# ---------------------------------------------------------------------------

class TestRunOptimisation:
    @patch("prototype.pre_approval.orchestrator.compute_optimal_split")
    def test_passes_correct_args(self, mock_compute):
        mock_compute.return_value = {
            "optimal_split": {"road_containers": 80, "sea_containers": 40, "total_transport_cost": 7500},
            "confidence": 0.92,
            "escalation_flags": [],
        }
        state = {"tuas_vessel_departure": "2026-08-19T20:00:00+08:00"}
        candidates = {"containers": [{"size": "40ft"}]}
        road = {"available_trucks": 20}
        sea = {"available_capacity_teu": 180}

        result = _run_optimisation(state, candidates, road, sea)

        mock_compute.assert_called_once_with(
            problem_id="PB-12",
            candidates=[{"size": "40ft"}],
            road_capacity=road,
            sea_capacity=sea,
            tuas_vessel_departure="2026-08-19T20:00:00+08:00",
        )
        assert result["confidence"] == 0.92

    @patch("prototype.pre_approval.orchestrator.compute_optimal_split")
    def test_returns_split_result(self, mock_compute):
        mock_compute.return_value = {"status": "success", "optimal_split": {"road_containers": 60}}
        result = _run_optimisation(
            {"tuas_vessel_departure": "2026-08-19T20:00:00+08:00"},
            {"containers": []},
            {},
            {},
        )
        assert result["status"] == "success"


# ---------------------------------------------------------------------------
# run_pre_approval_pipeline (integration)
# ---------------------------------------------------------------------------

class TestRunPreApprovalPipeline:
    @pytest.mark.asyncio
    @patch("prototype.pre_approval.orchestrator._run_optimisation")
    @patch("prototype.pre_approval.orchestrator._gather_parallel")
    async def test_full_happy_path(self, mock_parallel, mock_opt, valid_event, mock_split_result):
        mock_parallel.return_value = (
            {"containers": [], "container_breakdown": {"40ft_feu": 40, "20ft_teu": 80}},
            {"available_trucks": 20},
            {"available_capacity_teu": 180},
        )
        mock_opt.return_value = mock_split_result

        result = await run_pre_approval_pipeline(valid_event)

        assert isinstance(result, PreApprovalResult)
        assert result.run_id.startswith("run-")
        assert result.event["vessel_id"] == "MV PACIFIC STAR"
        assert result.split_result["confidence"] == 0.92
        mock_parallel.assert_called_once()
        mock_opt.assert_called_once()

    @pytest.mark.asyncio
    @patch("prototype.pre_approval.orchestrator._run_optimisation")
    @patch("prototype.pre_approval.orchestrator._gather_parallel")
    async def test_agent_state_populated(self, mock_parallel, mock_opt, valid_event, mock_split_result):
        mock_parallel.return_value = ({}, {}, {})
        mock_opt.return_value = mock_split_result

        result = await run_pre_approval_pipeline(valid_event)

        state = result.agent_state
        assert state["vessel_id"] == "MV PACIFIC STAR"
        assert state["container_count"] == 120
        assert state["origin_terminal"] == "PPT"
        assert state["current_step"] == "ingest"

    @pytest.mark.asyncio
    @patch("prototype.pre_approval.orchestrator._run_optimisation")
    @patch("prototype.pre_approval.orchestrator._gather_parallel")
    async def test_event_serialized_in_result(self, mock_parallel, mock_opt, valid_event, mock_split_result):
        mock_parallel.return_value = ({}, {}, {})
        mock_opt.return_value = mock_split_result

        result = await run_pre_approval_pipeline(valid_event)

        assert isinstance(result.event, dict)
        assert result.event["event_type"] == "ITT_COORDINATION_REQUEST"
        assert result.event["source"] == "CITOS_PPT"

    @pytest.mark.asyncio
    async def test_invalid_event_raises(self):
        bad_event = _make_valid_event(container_count=5, containers_ready=5)
        with pytest.raises(ValueError, match="Webhook validation failed"):
            await run_pre_approval_pipeline(bad_event)

    @pytest.mark.asyncio
    @patch("prototype.pre_approval.orchestrator._run_optimisation")
    @patch("prototype.pre_approval.orchestrator._gather_parallel")
    async def test_run_id_is_unique_per_invocation(self, mock_parallel, mock_opt, valid_event, mock_split_result):
        mock_parallel.return_value = ({}, {}, {})
        mock_opt.return_value = mock_split_result

        r1 = await run_pre_approval_pipeline(valid_event)
        r2 = await run_pre_approval_pipeline(valid_event)
        assert r1.run_id != r2.run_id

    @pytest.mark.asyncio
    @patch("prototype.pre_approval.orchestrator._run_optimisation")
    @patch("prototype.pre_approval.orchestrator._gather_parallel")
    async def test_pipeline_passes_parallel_results_to_optimisation(
        self, mock_parallel, mock_opt, valid_event, mock_split_result
    ):
        candidates = {"containers": [{"size": "20ft"}], "total_containers": 50}
        road = {"available_trucks": 15, "transit_time_minutes": 60}
        sea = {"available_capacity_teu": 90}
        mock_parallel.return_value = (candidates, road, sea)
        mock_opt.return_value = mock_split_result

        await run_pre_approval_pipeline(valid_event)

        call_args = mock_opt.call_args
        assert call_args[0][1] == candidates  # candidates
        assert call_args[0][2] == road  # road_capacity
        assert call_args[0][3] == sea  # sea_capacity

    @pytest.mark.asyncio
    @patch("prototype.pre_approval.orchestrator._run_optimisation")
    @patch("prototype.pre_approval.orchestrator._gather_parallel")
    async def test_split_result_in_output(self, mock_parallel, mock_opt, valid_event):
        mock_parallel.return_value = ({}, {}, {})
        split = {
            "status": "success",
            "optimal_split": {"road_containers": 60, "sea_containers": 60, "total_transport_cost": 9000},
            "confidence": 0.88,
            "escalation_flags": [{"trigger_id": "esc_1"}],
        }
        mock_opt.return_value = split

        result = await run_pre_approval_pipeline(valid_event)

        assert result.split_result is split
        assert result.split_result["optimal_split"]["road_containers"] == 60
        assert len(result.split_result["escalation_flags"]) == 1

    @pytest.mark.asyncio
    @patch("prototype.pre_approval.orchestrator._run_optimisation")
    @patch("prototype.pre_approval.orchestrator._gather_parallel")
    async def test_to_dict_roundtrip(self, mock_parallel, mock_opt, valid_event, mock_split_result):
        mock_parallel.return_value = ({}, {}, {})
        mock_opt.return_value = mock_split_result

        result = await run_pre_approval_pipeline(valid_event)
        d = result.to_dict()

        assert d["run_id"] == result.run_id
        assert d["event"]["vessel_id"] == "MV PACIFIC STAR"
        assert d["agent_state"]["current_step"] == "ingest"
        assert d["split_result"]["confidence"] == 0.92
