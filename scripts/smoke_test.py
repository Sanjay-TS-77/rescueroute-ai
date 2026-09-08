from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from rescueroute.web import app

client = TestClient(app)

health = client.get("/api/health")
health.raise_for_status()

client.post("/api/reset").raise_for_status()
created = client.post("/api/rescues", json={
    "donor_name": "ABC Bakery",
    "sandwiches": 42,
    "bread_loaves": 18,
    "pickup_deadline": "20:30",
    "contains_nuts": False,
    "requires_refrigeration": False,
    "mode": "deterministic",
})
created.raise_for_status()
event = created.json()
assert event["status"] == "COORDINATED"
assert event["unallocated_meals"] == 0

recovered = client.post(f"/api/rescues/{event['event_id']}/cancel-volunteer", json={})
recovered.raise_for_status()
assert recovered.json()["recovery"]["recovered"] is True

print(f"Smoke test passed: {event['event_id']} coordinated and autonomously recovered")
