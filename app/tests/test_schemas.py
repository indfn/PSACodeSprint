"""Tests for canonical Pydantic schemas (app/shared/models.py)."""

import pytest
from pydantic import ValidationError

from app.shared.models import (
    Container,
    ContainerBreakdown,
    DepartureWindow,
    FeederDownstreamConstraints,
    ITTCoordinationEvent,
    ITTSplitResponse,
    ITTSplitOption,
    ITTSplitTimeline,
    LoadingSequenceResponse,
    QcAdjustment,
    RoadITTCapacityResponse,
    SeaITTCapacityResponse,
    WebhookResponse,
)


def test_container_serialization():
    c = Container(
        container_id="MSKU1234567",
        size="40ft",
        yard_block="B-07",
        yard_position="Bay 01 Row 01 Tier 01",
        weight_kg=25000,
        priority="high",
        consignee="DB Schenker",
        destination_port="LA",
    )
    d = c.model_dump()
    assert d["container_id"] == "MSKU1234567"
    # round-trip
    c2 = Container.model_validate(d)
    assert c2.container_id == c.container_id


def test_container_invalid_size():
    with pytest.raises(ValidationError):
        Container(
            container_id="MSKU1234567",
            size="30ft",
            yard_block="B-07",
            yard_position="Bay 01",
            weight_kg=25000,
            priority="high",
            consignee="DB",
            destination_port="LA",
        )


def test_itt_coordination_event_valid():
    evt = ITTCoordinationEvent(
        event_type="ITT_COORDINATION_REQUEST",
        timestamp="2026-08-19T10:30:00+08:00",
        source="CITOS_PPT",
        priority="high",
        vessel_id="MV PACIFIC STAR",
        tuas_vessel_departure="2026-08-19T20:00:00+08:00",
        container_count=120,
        containers_ready=120,
        blocks_affected=["B-07", "B-08"],
        requested_by="Planner",
    )
    assert evt.container_count == 120
    assert evt.model_dump()["vessel_id"] == "MV PACIFIC STAR"


def test_itt_coordination_event_container_count_too_low():
    with pytest.raises(ValidationError):
        ITTCoordinationEvent(
            event_type="ITT_COORDINATION_REQUEST",
            timestamp="2026-08-19T10:30:00+08:00",
            source="CITOS_PPT",
            priority="high",
            vessel_id="MV TEST",
            tuas_vessel_departure="2026-08-19T20:00:00+08:00",
            container_count=10,  # <50 should fail ge=50
            containers_ready=10,
            blocks_affected=["B-07"],
            requested_by="Planner",
        )


def test_breakdown_alias():
    bd = ContainerBreakdown.model_validate({"40ft_feu": 40, "20ft_teu": 80})
    assert bd.fortyft_feu == 40
    d = bd.model_dump(by_alias=True)
    assert d["40ft_feu"] == 40


def test_itt_split_response_roundtrip():
    opt = ITTSplitOption(
        road_containers=80,
        road_breakdown="40x 40ft + 40x 20ft",
        road_trips=60,
        road_cost=9000,
        sea_containers=40,
        sea_terminal_handling_cost=1400,
        total_transport_cost=10400,
    )
    tl = ITTSplitTimeline(
        road_itt_arrival="2026-08-19T14:30:00+08:00",
        sea_itt_arrival="2026-08-19T16:30:00+08:00",
        tuas_loading_start="2026-08-19T17:00:00+08:00",
        vessel_departure="2026-08-19T20:00:00+08:00",
        margin_minutes=180,
    )
    resp = ITTSplitResponse(
        optimal_split=opt,
        alternatives=[opt],
        timeline=tl,
        cost_vs_baseline={"baseline_all_road_cost": 12000, "optimised_transport_cost": 10400},
    )
    d = resp.model_dump()
    assert d["optimal_split"]["road_containers"] == 80
    # validate again
    resp2 = ITTSplitResponse.model_validate(d)
    assert resp2.timeline.margin_minutes == 180


def test_road_and_sea_responses():
    road = RoadITTCapacityResponse(
        available_trucks=20,
        transit_time_minutes=90,
        road_conditions={"AYE": "normal"},
        cost_per_trip=150,
        lta_chassis_limits="1x 40ft/45ft (FEU) OR up to 2x 20ft (TEU) per prime mover",
        estimated_round_trip_minutes=210,
        earliest_departure="2026-08-19T11:00:00+08:00",
        latest_arrival_at_tuas="2026-08-19T18:00:00+08:00",
    )
    assert road.available_trucks == 20

    sea = SeaITTCapacityResponse(
        feeder_id="FEEDER ATLANTIC-03",
        feeder_operator="PIL",
        capacity_teu=800,
        current_occupancy_teu=620,
        available_capacity_teu=180,
        berth_status="berthed",
        departure_window=DepartureWindow(earliest="2026-08-19T14:00:00+08:00", latest="2026-08-19T16:00:00+08:00", requested="2026-08-19T14:00:00+08:00"),
        downstream_constraints=FeederDownstreamConstraints(destination_port="Port Klang", tidal_window="2026-08-19T23:00:00+08:00", transit_time_hours=18, must_depart_by="2026-08-19T05:00:00+08:00"),
        hold_cost_per_hour=800,
        missed_connection_cost=5000,
    )
    assert sea.feeder_id == "FEEDER ATLANTIC-03"


def test_loading_sequence_response():
    r = LoadingSequenceResponse(
        vessel_id="MV PACIFIC STAR",
        original_loading_sequence="Bay14→Bay12→Bay10→Bay08",
        updated_loading_sequence="Bay14(road@14:30)→Bay12(road@14:30)→Bay10(sea@16:30)→Bay08(sea@16:30)",
        estimated_loading_completion="2026-08-19T19:30:00+08:00",
        qc_adjustments=[QcAdjustment(qc_id="QC-07", original_bay="Bay14", new_bay="Bay14", eta="14:30")],
    )
    assert r.status == "success"
    assert len(r.qc_adjustments) == 1


def test_webhook_response():
    wr = WebhookResponse(status="accepted", run_id="run-abc123")
    assert wr.run_id == "run-abc123"
    d = wr.model_dump()
    assert d["status"] == "accepted"


def test_webhook_event_alias():
    # WebhookEvent should be alias to ITTCoordinationEvent
    from app.shared.models import WebhookEvent
    assert WebhookEvent is ITTCoordinationEvent
