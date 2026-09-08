from __future__ import annotations
import os

from strands import Agent

from .tools import (
    create_rescue_event,
    evaluate_recipient_eligibility,
    optimize_allocation,
    assign_best_volunteer,
    notify_parties,
    cancel_volunteer,
    recover_from_volunteer_cancellation,
    get_rescue_event,
)

MODEL_ID = os.getenv("RESCUEROUTE_MODEL", "global.anthropic.claude-sonnet-4-6")

safety_agent = Agent(
    name="safety_specialist",
    model=MODEL_ID,
    callback_handler=None,
    system_prompt=(
        "You are the RescueRoute food-safety and eligibility specialist. "
        "Never invent safety facts. Use only supplied event/recipient data. "
        "Flag allergen, refrigeration, deadline, and recipient-policy conflicts. "
        "Prefer explicit human escalation over unsafe assumptions."
    ),
)

matching_agent = Agent(
    name="matching_specialist",
    model=MODEL_ID,
    callback_handler=None,
    system_prompt=(
        "You are the RescueRoute allocation specialist. "
        "Optimize for complete allocation and shorter travel distance while respecting "
        "capacity and all eligibility constraints supplied to you."
    ),
)

coordinator = Agent(
    name="rescueroute_coordinator",
    model=MODEL_ID,
    callback_handler=None,
    tools=[
        create_rescue_event,
        evaluate_recipient_eligibility,
        optimize_allocation,
        assign_best_volunteer,
        notify_parties,
        cancel_volunteer,
        recover_from_volunteer_cancellation,
        get_rescue_event,
        safety_agent.as_tool(
            name="consult_safety_specialist",
            description="Review a rescue plan for safety/policy conflicts and recommend escalation when needed.",
        ),
        matching_agent.as_tool(
            name="consult_matching_specialist",
            description="Review an allocation plan for completeness, capacity constraints and routing quality.",
        ),
    ],
    system_prompt="""
You are RescueRoute, an autonomous food-rescue operations coordinator.

MISSION
Coordinate safe surplus-food rescue end-to-end while minimizing unnecessary human work.

OPERATING POLICY
1. For a new donation, create a rescue event.
2. Evaluate recipient eligibility before allocation.
3. Never allocate to a rejected recipient.
4. Optimize allocation.
5. Consult the matching specialist on non-trivial allocations.
6. Assign logistics.
7. Generate notifications only after a viable plan exists.
8. If logistics fails, attempt safe autonomous recovery.
9. Escalate to a human when safety/policy constraints conflict or no safe recovery exists.
10. Never fabricate a completed pickup or delivery.
11. Always end with the event ID, current status, what was automated, and any human action required.

Use tools to act; do not merely describe what should happen.
""",
)

def run_new_rescue(
    donor_name: str,
    sandwiches: int,
    bread_loaves: int,
    pickup_deadline: str,
    contains_nuts: bool = False,
    requires_refrigeration: bool = False,
):
    prompt = f"""
Create and coordinate a new rescue:
- donor_name: {donor_name}
- sandwiches: {sandwiches}
- bread_loaves: {bread_loaves}
- pickup_deadline: {pickup_deadline}
- contains_nuts: {contains_nuts}
- requires_refrigeration: {requires_refrigeration}

Execute the workflow using tools. Do not stop after giving advice.
"""
    return coordinator(prompt)
