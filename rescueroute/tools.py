from __future__ import annotations

from strands import tool

from . import engine


@tool
def create_rescue_event(
    donor_name: str,
    sandwiches: int,
    bread_loaves: int,
    pickup_deadline: str,
    contains_nuts: bool = False,
    requires_refrigeration: bool = False,
) -> dict:
    """Create a new rescue event from a donor's surplus-food report."""
    return engine.create_event(
        donor_name=donor_name,
        sandwiches=sandwiches,
        bread_loaves=bread_loaves,
        pickup_deadline=pickup_deadline,
        contains_nuts=contains_nuts,
        requires_refrigeration=requires_refrigeration,
    )


@tool
def evaluate_recipient_eligibility(event_id: str) -> dict:
    """Apply hard food-safety, recipient-policy, deadline and storage constraints."""
    return engine.evaluate_eligibility(event_id)


@tool
def optimize_allocation(event_id: str) -> dict:
    """Allocate meals to eligible recipients under capacity and distance constraints."""
    return engine.optimize_allocation(event_id)


@tool
def assign_best_volunteer(event_id: str) -> dict:
    """Assign the best currently available volunteer for the rescue route."""
    return engine.assign_volunteer(event_id)


@tool
def notify_parties(event_id: str) -> dict:
    """Generate donor, recipient and volunteer notifications for the current plan."""
    return engine.generate_notifications(event_id)


@tool
def cancel_volunteer(event_id: str) -> dict:
    """Simulate the currently assigned volunteer cancelling the rescue."""
    return engine.cancel_assigned_volunteer(event_id)


@tool
def recover_from_volunteer_cancellation(event_id: str) -> dict:
    """Attempt a safe autonomous recovery after a volunteer cancellation."""
    return engine.recover_logistics(event_id)


@tool
def approve_human_action(event_id: str, note: str = "Approved by human operator") -> dict:
    """Record explicit human approval for a rescue that is paused for review."""
    return engine.approve_human_action(event_id, note)


@tool
def get_rescue_event(event_id: str) -> dict:
    """Return the current rescue event state and audit trail."""
    return engine.get_event(event_id)
