import pytest
from fastapi.testclient import TestClient

from rescueroute.store import reset_state
from rescueroute.web import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_state():
    reset_state()


def _create(**overrides):
    payload = {
        "donor_name": "ABC Bakery",
        "sandwiches": 42,
        "bread_loaves": 18,
        "pickup_deadline": "20:30",
        "contains_nuts": False,
        "requires_refrigeration": False,
        "mode": "deterministic",
    }
    payload.update(overrides)
    return client.post("/api/rescues", json=payload)


def test_health_endpoint_reports_service():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["service"] == "rescueroute-ai"


def test_api_rejects_invalid_24h_time():
    response = _create(pickup_deadline="29:99")
    assert response.status_code == 422


def test_api_coordinates_standard_rescue():
    response = _create()
    assert response.status_code == 200
    event = response.json()
    assert event["status"] == "COORDINATED"
    assert event["estimated_meals"] == 114
    assert event["unallocated_meals"] == 0


def test_api_autonomous_recovery_uses_backup_volunteer():
    event = _create().json()
    response = client.post(f"/api/rescues/{event['event_id']}/cancel-volunteer", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["recovery"]["recovered"] is True
    assert body["event"]["status"] == "RECOVERED_NEW_VOLUNTEER"
    assert body["event"]["volunteer"]["id"] == "VOL-2"


def test_demo_exhaustion_escalates_without_unsafe_guessing():
    event = _create().json()
    response = client.post(
        f"/api/demo/rescues/{event['event_id']}/force-logistics-escalation",
        json={},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["demo_only"] is True
    assert body["recovery"]["recovered"] is False
    assert body["event"]["status"] == "HUMAN_REVIEW"
    assert body["event"]["human_approval_required"] is True
