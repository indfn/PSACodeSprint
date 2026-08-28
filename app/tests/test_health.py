"""Health endpoint tests — uses shared fixture from conftest.py."""

# Uses `client` fixture from app/tests/conftest.py (function-scoped TestClient)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["service"] == "psa-nexus"


def test_root(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (200, 307)
    if r.status_code == 307:
        assert "/ui" in r.headers.get("location", "")
    else:
        assert "PSA Nexus" in r.text


def test_mock_citos_ppt(client):
    r = client.get("/api/citos/ppt/containers")
    assert r.status_code == 200
    assert r.json()["status"] == "success"
    assert r.json()["total_containers"] == 120


def test_mock_optetruck(client):
    r = client.get("/api/optetruck/capacity")
    assert r.status_code == 200
    assert r.json()["status"] == "success"
    assert r.json()["available_trucks"] == 50


def test_mock_feeder(client):
    r = client.get("/api/feeder/FEEDER%20ATLANTIC-03")
    assert r.status_code == 200
    assert r.json()["status"] == "success"
    assert r.json()["feeder_id"] == "FEEDER ATLANTIC-03"


def test_mock_portnet(client):
    r = client.get("/api/portnet/feeder/FEEDER%20ATLANTIC-03")
    assert r.status_code == 200
    assert r.json()["status"] == "success"
    assert r.json()["portnet_source"] == "community_sync"


def test_webhook_runs(client):
    r = client.get("/webhook/runs")
    assert r.status_code == 200
    assert "runs" in r.json()
