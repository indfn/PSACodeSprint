import asyncio

import pytest

from app.tools.optimiser import OptimiserTool, compute_roi
from app.mocks.data import get_container_data, get_truck_data, get_feeder_data


def test_compute_roi_direct():
    roi = compute_roi(12000, 10400)
    assert roi["per_incident"] == 8000
    assert roi["per_incident_numeric"] == 8000
    assert roi["per_incident_transport_only"] == 1600
    assert roi["transport_savings"] == 1600
    assert roi["monthly"] == "$32K-$48K"
    assert roi["annual"] == "$384K-$576K"
    assert roi["cluster_annual"] == "$1.26M-$2.08M"
    assert roi["monthly_low"] == 32000
    assert roi["monthly_high"] == 48000
    assert roi["annual_low"] == 384000
    assert roi["annual_high"] == 576000
    assert roi["cluster_low"] == 1260000
    assert roi["cluster_high"] == 2080000


def test_compute_roi_custom_values():
    roi = compute_roi(10000, 8000)
    assert roi["per_incident_transport_only"] == 2000
    assert roi["baseline"] == 10000
    assert roi["optimised"] == 8000


def test_optimiser_cost_vs_baseline_and_roi():
    tool = OptimiserTool()
    candidates = get_container_data()
    road = get_truck_data()
    sea = get_feeder_data()
    result = asyncio.run(
        tool.call(
            candidates=candidates,
            road_capacity=road,
            sea_capacity=sea,
            tuas_vessel_departure="2026-08-19T20:00:00+08:00",
            _run_id="test-roi",
        )
    )
    out = result.output
    cvb = out["cost_vs_baseline"]
    assert cvb["baseline_all_road"] == 12000
    assert cvb["baseline_all_road_cost"] == 12000
    assert cvb["baseline"] == 12000
    assert cvb["optimised"] == 10400
    assert cvb["optimised_transport_cost"] == 10400
    assert cvb["savings"] == 1600
    assert cvb["transport_savings"] == 1600
    assert cvb["direct_transport_savings"] == 1600
    assert cvb["baseline_all_road_trips"] == 80
    assert out["optimal_split"]["total_transport_cost"] == 10400
    assert out["optimal_split"]["road_containers"] == 80
    assert out["optimal_split"]["sea_containers"] == 40
    roi = out["roi"]
    assert roi["per_incident"] == 8000
    assert roi["per_incident_numeric"] == 8000
    assert roi["per_incident_transport_only"] == 1600
    assert roi["monthly_low"] == 32000
    assert roi["monthly_high"] == 48000
    assert roi["annual_low"] == 384000
    assert roi["annual_high"] == 576000
    assert roi["cluster_low"] == 1260000
    assert roi["cluster_high"] == 2080000
