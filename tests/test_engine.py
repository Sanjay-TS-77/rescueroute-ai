import pytest

from rescueroute import engine
from rescueroute.store import VOLUNTEERS, reset_state


@pytest.fixture(autouse=True)
def fresh_state():
    reset_state()


def test_standard_rescue_fully_allocates_and_coordinates():
    event = engine.coordinate_rescue(
        donor_name="ABC Bakery", sandwiches=42, bread_loaves=18, pickup_deadline="20:30"
    )
    assert event["estimated_meals"] == 114
    assert event["unallocated_meals"] == 0
    assert event["status"] == "COORDINATED"
    assert event["volunteer"]["id"] == "VOL-1"
    assert not event["human_approval_required"]


def test_nut_policy_blocks_shelter():
    event = engine.create_event("Bakery", 20, 0, "20:00", contains_nuts=True)
    result = engine.evaluate_eligibility(event["event_id"])
    assert "SH-B" in {r["id"] for r in result["rejected"]}


def test_refrigeration_blocks_non_refrigerated_recipient():
    event = engine.create_event("Cafe", 20, 0, "20:00", requires_refrigeration=True)
    result = engine.evaluate_eligibility(event["event_id"])
    assert "SH-B" in {r["id"] for r in result["rejected"]}


def test_capacity_is_never_exceeded():
    event = engine.coordinate_rescue("Event", 100, 10, "20:00")
    caps = {"FB-A": 25, "SH-B": 40, "CK-C": 60}
    assert all(a["meals"] <= caps[a["recipient_id"]] for a in event["allocation"])


def test_partial_allocation_escalates_to_human():
    event = engine.coordinate_rescue("Large Donor", 150, 0, "20:00")
    assert event["unallocated_meals"] > 0
    assert event["human_approval_required"]
    assert event["status"] == "HUMAN_REVIEW"


def test_volunteer_cancellation_autonomously_recovers_with_backup():
    event = engine.coordinate_rescue("Bakery", 42, 18, "20:30")
    assert event["volunteer"]["id"] == "VOL-1"
    engine.cancel_assigned_volunteer(event["event_id"])
    recovery = engine.recover_logistics(event["event_id"])
    assert recovery["recovered"]
    assert recovery["method"] == "replacement_volunteer"
    assert recovery["volunteer"]["id"] == "VOL-2"


def test_no_safe_recovery_escalates():
    event = engine.coordinate_rescue("Bakery", 42, 18, "20:30")
    for volunteer in VOLUNTEERS:
        volunteer["available"] = False
    engine.cancel_assigned_volunteer(event["event_id"])
    recovery = engine.recover_logistics(event["event_id"])
    assert not recovery["recovered"]
    assert recovery["human_approval_required"]
