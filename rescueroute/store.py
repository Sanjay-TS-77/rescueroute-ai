from __future__ import annotations
from copy import deepcopy
from typing import Any

RECIPIENTS = [
    {
        "id": "FB-A",
        "name": "Hope Food Bank",
        "distance_km": 2.1,
        "capacity_meals": 25,
        "open_until": "21:00",
        "accepts_nuts": True,
        "self_pickup": False,
        "refrigeration": True,
    },
    {
        "id": "SH-B",
        "name": "Sunrise Shelter",
        "distance_km": 4.2,
        "capacity_meals": 40,
        "open_until": "22:00",
        "accepts_nuts": False,
        "self_pickup": True,
        "refrigeration": False,
    },
    {
        "id": "CK-C",
        "name": "Community Kitchen",
        "distance_km": 6.1,
        "capacity_meals": 60,
        "open_until": "23:00",
        "accepts_nuts": True,
        "self_pickup": True,
        "refrigeration": True,
    },
]

VOLUNTEERS = [
    {"id": "VOL-1", "name": "Maya", "available": True, "max_km": 15},
    {"id": "VOL-2", "name": "Arun", "available": True, "max_km": 20},
]

STATE: dict[str, Any] = {
    "events": {},
    "notifications": [],
    "counter": 1041,
}

def reset_state() -> None:
    STATE["events"] = {}
    STATE["notifications"] = []
    STATE["counter"] = 1041
    for volunteer in VOLUNTEERS:
        volunteer["available"] = True

def snapshot() -> dict[str, Any]:
    return {
        "recipients": deepcopy(RECIPIENTS),
        "volunteers": deepcopy(VOLUNTEERS),
        "state": deepcopy(STATE),
    }
