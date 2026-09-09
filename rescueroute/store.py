from __future__ import annotations

import json
import os
from copy import deepcopy
from functools import lru_cache
from typing import Any

import boto3

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

TABLE_NAME = os.getenv("RESCUEROUTE_TABLE", "").strip()
AWS_REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"


@lru_cache(maxsize=1)
def _table():
    if not TABLE_NAME:
        return None
    return boto3.resource("dynamodb", region_name=AWS_REGION).Table(TABLE_NAME)


def using_dynamodb() -> bool:
    return bool(TABLE_NAME)


def next_event_id() -> str:
    table = _table()
    if table is None:
        STATE["counter"] += 1
        return f"FR-{STATE['counter']}"

    response = table.update_item(
        Key={"event_id": "__COUNTER__"},
        UpdateExpression="ADD event_counter :one SET entity_type = :counter_type",
        ExpressionAttributeValues={":one": 1, ":counter_type": "counter"},
        ReturnValues="UPDATED_NEW",
    )
    counter = int(response["Attributes"]["event_counter"])
    if counter < 1042:
        # A brand-new table starts at 1. Raise it once to preserve the familiar demo IDs.
        response = table.update_item(
            Key={"event_id": "__COUNTER__"},
            UpdateExpression="SET event_counter = :base, entity_type = :counter_type",
            ExpressionAttributeValues={":base": 1042, ":counter_type": "counter"},
            ReturnValues="ALL_NEW",
        )
        counter = int(response["Attributes"]["event_counter"])
    return f"FR-{counter}"


def save_event(event: dict[str, Any]) -> dict[str, Any]:
    table = _table()
    if table is None:
        STATE["events"][event["event_id"]] = deepcopy(event)
        return event

    table.put_item(
        Item={
            "event_id": event["event_id"],
            "entity_type": "event",
            "status": str(event.get("status", "UNKNOWN")),
            "payload": json.dumps(event, separators=(",", ":"), ensure_ascii=False),
        }
    )
    return event


def load_event(event_id: str) -> dict[str, Any]:
    table = _table()
    if table is None:
        try:
            return deepcopy(STATE["events"][event_id])
        except KeyError as exc:
            raise ValueError(f"Unknown rescue event: {event_id}") from exc

    response = table.get_item(Key={"event_id": event_id}, ConsistentRead=True)
    item = response.get("Item")
    if not item or item.get("entity_type") != "event":
        raise ValueError(f"Unknown rescue event: {event_id}")
    return json.loads(item["payload"])


def list_events() -> list[dict[str, Any]]:
    table = _table()
    if table is None:
        return [deepcopy(item) for item in STATE["events"].values()]

    items: list[dict[str, Any]] = []
    kwargs: dict[str, Any] = {}
    while True:
        response = table.scan(**kwargs)
        for item in response.get("Items", []):
            if item.get("entity_type") == "event" and item.get("payload"):
                items.append(json.loads(item["payload"]))
        key = response.get("LastEvaluatedKey")
        if not key:
            break
        kwargs["ExclusiveStartKey"] = key
    return sorted(items, key=lambda item: item.get("event_id", ""))


def reset_state() -> None:
    table = _table()
    if table is None:
        STATE["events"] = {}
        STATE["notifications"] = []
        STATE["counter"] = 1041
    else:
        keys: list[str] = []
        kwargs: dict[str, Any] = {"ProjectionExpression": "event_id"}
        while True:
            response = table.scan(**kwargs)
            keys.extend(item["event_id"] for item in response.get("Items", []))
            key = response.get("LastEvaluatedKey")
            if not key:
                break
            kwargs["ExclusiveStartKey"] = key
        if keys:
            with table.batch_writer() as batch:
                for event_id in keys:
                    batch.delete_item(Key={"event_id": event_id})
        table.put_item(Item={"event_id": "__COUNTER__", "entity_type": "counter", "event_counter": 1041})

    for volunteer in VOLUNTEERS:
        volunteer["available"] = True


def snapshot() -> dict[str, Any]:
    return {
        "recipients": deepcopy(RECIPIENTS),
        "volunteers": deepcopy(VOLUNTEERS),
        "state": {
            "events": list_events(),
            "notifications": deepcopy(STATE["notifications"]),
            "counter": STATE["counter"],
            "backend": "dynamodb" if using_dynamodb() else "memory",
        },
    }
