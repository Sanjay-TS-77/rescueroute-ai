from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .store import RECIPIENTS, VOLUNTEERS, STATE


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event(event_id: str) -> dict[str, Any]:
    try:
        return STATE["events"][event_id]
    except KeyError as exc:
        raise ValueError(f"Unknown rescue event: {event_id}") from exc


def create_event(
    donor_name: str,
    sandwiches: int,
    bread_loaves: int,
    pickup_deadline: str,
    contains_nuts: bool = False,
    requires_refrigeration: bool = False,
) -> dict[str, Any]:
    if sandwiches < 0 or bread_loaves < 0:
        raise ValueError("Food quantities cannot be negative.")
    if sandwiches == 0 and bread_loaves == 0:
        raise ValueError("At least one food quantity must be positive.")
    try:
        datetime.strptime(pickup_deadline, "%H:%M")
    except (TypeError, ValueError) as exc:
        raise ValueError("pickup_deadline must be a valid 24-hour HH:MM time.") from exc

    donor_name = donor_name.strip()
    if not donor_name:
        raise ValueError("donor_name cannot be blank.")

    STATE["counter"] += 1
    event_id = f"FR-{STATE['counter']}"
    meals = sandwiches + bread_loaves * 4
    event = {
        "event_id": event_id,
        "donor_name": donor_name,
        "sandwiches": sandwiches,
        "bread_loaves": bread_loaves,
        "estimated_meals": meals,
        "pickup_deadline": pickup_deadline,
        "contains_nuts": contains_nuts,
        "requires_refrigeration": requires_refrigeration,
        "status": "CREATED",
        "eligible_recipients": [],
        "rejected_recipients": [],
        "allocation": [],
        "unallocated_meals": meals,
        "volunteer": None,
        "human_approval_required": False,
        "approval_reason": None,
        "notifications": [],
        "audit": [{"at": _now(), "action": "event_created"}],
    }
    STATE["events"][event_id] = event
    return event


def evaluate_eligibility(event_id: str) -> dict[str, Any]:
    event = _event(event_id)
    eligible: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for recipient in RECIPIENTS:
        reasons: list[str] = []
        if event["contains_nuts"] and not recipient["accepts_nuts"]:
            reasons.append("nut-allergen-policy")
        if event["requires_refrigeration"] and not recipient["refrigeration"]:
            reasons.append("no-refrigeration")
        if recipient["open_until"] < event["pickup_deadline"]:
            reasons.append("closes-before-pickup-deadline")

        if reasons:
            rejected.append({
                "id": recipient["id"],
                "name": recipient["name"],
                "reasons": reasons,
            })
        else:
            eligible.append(recipient.copy())

    event["eligible_recipients"] = eligible
    event["rejected_recipients"] = rejected
    event["status"] = "ELIGIBILITY_CHECKED"
    event["audit"].append({
        "at": _now(),
        "action": "eligibility_checked",
        "eligible": [r["id"] for r in eligible],
        "rejected": rejected,
    })
    return {"event_id": event_id, "eligible": eligible, "rejected": rejected}


def optimize_allocation(event_id: str) -> dict[str, Any]:
    event = _event(event_id)
    if event["status"] not in {"ELIGIBILITY_CHECKED", "PARTIALLY_ALLOCATED", "ALLOCATED"}:
        raise ValueError("Run eligibility evaluation before allocation.")

    remaining = event["estimated_meals"]
    allocation: list[dict[str, Any]] = []
    for recipient in sorted(event["eligible_recipients"], key=lambda r: r["distance_km"]):
        if remaining <= 0:
            break
        qty = min(remaining, recipient["capacity_meals"])
        if qty > 0:
            allocation.append({
                "recipient_id": recipient["id"],
                "recipient_name": recipient["name"],
                "meals": qty,
                "distance_km": recipient["distance_km"],
            })
            remaining -= qty

    event["allocation"] = allocation
    event["unallocated_meals"] = remaining
    if remaining == 0:
        event["status"] = "ALLOCATED"
    else:
        event["status"] = "PARTIALLY_ALLOCATED"
        event["human_approval_required"] = True
        blockers = [item for item in event["rejected_recipients"] if item["reasons"]]
        if blockers:
            event["approval_reason"] = (
                f"{remaining} meals remain unallocated because safety/policy constraints "
                "exclude otherwise available capacity. Human coordination is required."
            )
        else:
            event["approval_reason"] = (
                f"{remaining} meals exceed currently eligible recipient capacity. "
                "Human coordination is required."
            )

    event["audit"].append({
        "at": _now(),
        "action": "allocation_optimized",
        "allocation": allocation,
        "unallocated_meals": remaining,
    })
    return {
        "event_id": event_id,
        "allocation": allocation,
        "unallocated_meals": remaining,
        "fully_allocated": remaining == 0,
        "human_approval_required": event["human_approval_required"],
        "approval_reason": event["approval_reason"],
    }


def assign_volunteer(event_id: str) -> dict[str, Any]:
    event = _event(event_id)
    if not event["allocation"]:
        raise ValueError("Allocate food before assigning logistics.")

    route_km = max(item["distance_km"] for item in event["allocation"])
    candidates = [
        volunteer for volunteer in VOLUNTEERS
        if volunteer["available"] and volunteer["max_km"] >= route_km
    ]
    if not candidates:
        event["status"] = "NO_VOLUNTEER"
        event["audit"].append({"at": _now(), "action": "no_volunteer_available"})
        return {"event_id": event_id, "assigned": False, "route_km": route_km}

    selected = sorted(candidates, key=lambda v: (v["max_km"], v["id"]))[0]
    event["volunteer"] = selected.copy()
    event["status"] = "VOLUNTEER_ASSIGNED"
    event["audit"].append({
        "at": _now(),
        "action": "volunteer_assigned",
        "volunteer_id": selected["id"],
    })
    return {"event_id": event_id, "assigned": True, "volunteer": selected.copy(), "route_km": route_km}


def generate_notifications(event_id: str) -> dict[str, Any]:
    event = _event(event_id)
    if not event["allocation"]:
        raise ValueError("No allocation exists to notify.")

    notes: list[dict[str, str]] = [{
        "audience": "donor",
        "message": (
            f"Rescue {event_id} coordinated for {event['donor_name']}; "
            f"pickup deadline {event['pickup_deadline']}."
        ),
    }]
    for allocation in event["allocation"]:
        notes.append({
            "audience": allocation["recipient_id"],
            "message": f"Incoming rescue {event_id}: {allocation['meals']} estimated meals.",
        })
    if event["volunteer"]:
        notes.append({
            "audience": event["volunteer"]["id"],
            "message": f"Assigned rescue {event_id}; pickup before {event['pickup_deadline']}.",
        })

    event["notifications"] = notes
    STATE["notifications"].extend(notes)
    event["audit"].append({"at": _now(), "action": "notifications_generated", "count": len(notes)})
    if event["human_approval_required"]:
        event["status"] = "HUMAN_REVIEW"
    else:
        event["status"] = "COORDINATED"
    return {"event_id": event_id, "notifications": notes, "status": event["status"]}


def cancel_assigned_volunteer(event_id: str) -> dict[str, Any]:
    event = _event(event_id)
    if not event["volunteer"]:
        return {"event_id": event_id, "cancelled": False, "reason": "No volunteer assigned."}

    volunteer_id = event["volunteer"]["id"]
    for volunteer in VOLUNTEERS:
        if volunteer["id"] == volunteer_id:
            volunteer["available"] = False

    event["volunteer"] = None
    event["status"] = "VOLUNTEER_CANCELLED"
    event["audit"].append({"at": _now(), "action": "volunteer_cancelled", "volunteer_id": volunteer_id})
    return {"event_id": event_id, "cancelled": True, "volunteer_id": volunteer_id}


def recover_logistics(event_id: str) -> dict[str, Any]:
    event = _event(event_id)
    route_km = max((item["distance_km"] for item in event["allocation"]), default=0)
    candidates = [v for v in VOLUNTEERS if v["available"] and v["max_km"] >= route_km]

    if candidates:
        selected = sorted(candidates, key=lambda v: (v["max_km"], v["id"]))[0]
        event["volunteer"] = selected.copy()
        event["status"] = "RECOVERED_NEW_VOLUNTEER"
        event["audit"].append({
            "at": _now(),
            "action": "recovered_with_replacement_volunteer",
            "volunteer_id": selected["id"],
        })
        return {
            "event_id": event_id,
            "recovered": True,
            "method": "replacement_volunteer",
            "volunteer": selected.copy(),
        }

    allocated_ids = {a["recipient_id"] for a in event["allocation"]}
    allocated_recipients = [r for r in RECIPIENTS if r["id"] in allocated_ids]
    if allocated_recipients and all(r["self_pickup"] for r in allocated_recipients):
        event["status"] = "RECOVERED_SELF_PICKUP"
        event["audit"].append({"at": _now(), "action": "recovered_by_recipient_self_pickup"})
        return {"event_id": event_id, "recovered": True, "method": "recipient_self_pickup"}

    event["human_approval_required"] = True
    event["approval_reason"] = (
        "No replacement volunteer is available and at least one allocated recipient "
        "cannot self-pickup. Human logistics coordination is required."
    )
    event["status"] = "HUMAN_REVIEW"
    event["audit"].append({"at": _now(), "action": "logistics_escalated_to_human"})
    return {
        "event_id": event_id,
        "recovered": False,
        "human_approval_required": True,
        "reason": event["approval_reason"],
    }


def approve_human_action(event_id: str, note: str = "Approved by human operator") -> dict[str, Any]:
    event = _event(event_id)
    if not event["human_approval_required"]:
        return {"event_id": event_id, "approved": False, "reason": "No approval is pending."}
    event["human_approval_required"] = False
    event["approval_reason"] = None
    event["status"] = "HUMAN_APPROVED"
    event["audit"].append({"at": _now(), "action": "human_approval", "note": note})
    return {"event_id": event_id, "approved": True, "status": event["status"]}


def get_event(event_id: str) -> dict[str, Any]:
    return _event(event_id)


def list_events() -> list[dict[str, Any]]:
    return list(STATE["events"].values())


def coordinate_rescue(
    donor_name: str,
    sandwiches: int,
    bread_loaves: int,
    pickup_deadline: str,
    contains_nuts: bool = False,
    requires_refrigeration: bool = False,
) -> dict[str, Any]:
    event = create_event(
        donor_name=donor_name,
        sandwiches=sandwiches,
        bread_loaves=bread_loaves,
        pickup_deadline=pickup_deadline,
        contains_nuts=contains_nuts,
        requires_refrigeration=requires_refrigeration,
    )
    event_id = event["event_id"]
    evaluate_eligibility(event_id)
    optimize_allocation(event_id)
    assign_volunteer(event_id)
    generate_notifications(event_id)
    return get_event(event_id)
