"""Integration tests for PSA Mock API Server."""

import pytest
from fastapi.testclient import TestClient
from prototype.main import app

client = TestClient(app)


# --- Health ---
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# --- CITOS PPT ---
def test_containers():
    response = client.get("/api/citos/ppt/containers")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_containers"] == 120
    assert len(data["containers"]) == 120
    assert data["dg_containers"] == 3


def test_containers_custom_vessel():
    response = client.get("/api/citos/ppt/containers?vessel_id=TEST")
    assert response.status_code == 200
    assert response.json()["vessel_id"] == "TEST"


# --- OptETruck ---
def test_truck_capacity():
    response = client.get("/api/optetruck/capacity")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["available_trucks"] == 20
    assert data["cost_per_trip"] == 150
    assert data["transit_time_minutes"] == 90


# --- Feeder ---
def test_feeder_capacity():
    response = client.get("/api/feeder/FEEDER%20ATLANTIC-03")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["feeder_id"] == "FEEDER ATLANTIC-03"
    assert data["capacity_teu"] == 800
    assert data["hold_cost_per_hour"] == 800


# --- CITOS Tuas ---
def test_loading_sequence():
    response = client.post(
        "/api/citos/tuas/loading-sequence",
        json={
            "vessel_id": "MV PACIFIC STAR",
            "itt_eta_road": "14:30",
            "itt_eta_sea": "16:30",
            "container_ids_road": ["MSKU7654321"],
            "container_ids_sea": ["TCLU1234567"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["vessel_id"] == "MV PACIFIC STAR"
    assert len(data["qc_adjustments"]) == 4


# --- PORTNET ---
def test_portnet_feeder():
    response = client.get("/api/portnet/feeder/FEEDER%20ATLANTIC-03")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["portnet_source"] == "community_sync"


# --- Webhook ---
def test_webhook_valid():
    payload = {
        "event_type": "ITT_COORDINATION_REQUEST",
        "timestamp": "2026-08-19T10:30:00+08:00",
        "source": "CITOS_PPT",
        "priority": "high",
        "origin_terminal": "PPT",
        "destination_terminal": "TUAS",
        "vessel_id": "MV PACIFIC STAR",
        "tuas_vessel_departure": "2026-08-19T20:00:00+08:00",
        "container_count": 120,
        "containers_ready": 120,
        "blocks_affected": ["B-07", "B-08", "B-12", "B-14"],
        "dg_containers": 3,
        "priority_containers": 45,
        "requested_by": "PPT_Yard_Planner_Lim",
        "notes": "Priority transhipment for MV PACIFIC STAR",
    }
    response = client.post("/webhook/itt-coordination", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert "run_id" in data
    assert data["run_id"].startswith("run-")


def test_webhook_rejects_low_container_count():
    payload = {
        "event_type": "ITT_COORDINATION_REQUEST",
        "timestamp": "2026-08-19T10:30:00+08:00",
        "source": "CITOS_PPT",
        "priority": "high",
        "origin_terminal": "PPT",
        "destination_terminal": "TUAS",
        "vessel_id": "MV PACIFIC STAR",
        "tuas_vessel_departure": "2026-08-19T20:00:00+08:00",
        "container_count": 30,
        "containers_ready": 30,
        "blocks_affected": ["B-07"],
        "dg_containers": 0,
        "priority_containers": 0,
        "requested_by": "test",
        "notes": "",
    }
    response = client.post("/webhook/itt-coordination", json=payload)
    # Pydantic ge=50 validation returns 422 before endpoint runs
    assert response.status_code == 422


def test_webhook_run_status():
    payload = {
        "event_type": "ITT_COORDINATION_REQUEST",
        "timestamp": "2026-08-19T10:30:00+08:00",
        "source": "CITOS_PPT",
        "priority": "high",
        "origin_terminal": "PPT",
        "destination_terminal": "TUAS",
        "vessel_id": "MV TEST",
        "tuas_vessel_departure": "2026-08-19T20:00:00+08:00",
        "container_count": 60,
        "containers_ready": 60,
        "blocks_affected": ["B-07"],
        "dg_containers": 0,
        "priority_containers": 0,
        "requested_by": "test",
        "notes": "",
    }
    create_response = client.post("/webhook/itt-coordination", json=payload)
    run_id = create_response.json()["run_id"]

    status_response = client.get(f"/webhook/runs/{run_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "accepted"
    assert status_response.json()["current_step"] == "ingest"


# --- Edge cases ---
def test_feeder_conflict_simulation():
    from prototype.mocks.edge_cases import simulate_feeder_conflict
    from prototype.mocks.data import get_feeder_data

    normal = get_feeder_data()
    conflicted = simulate_feeder_conflict(normal)

    assert conflicted["berth_status"] == "berth_conflict_delayed"
    assert conflicted["departure_window"]["earliest"] == "2026-08-19T16:00:00+08:00"
    assert conflicted["edge_case"] == "feeder_berth_conflict"


def test_stale_data_simulation():
    from prototype.mocks.edge_cases import simulate_stale_data
    from prototype.mocks.data import get_container_data

    normal = get_container_data()
    stale = simulate_stale_data(normal, stale_minutes=25)

    assert stale["data_age_minutes"] == 25
    assert stale["edge_case"] == "data_staleness"
