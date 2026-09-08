from __future__ import annotations

import json
import random
from pathlib import Path

from . import engine
from .store import RECIPIENTS, VOLUNTEERS, reset_state


def _safety_scenarios(rng: random.Random, scenarios: int) -> tuple[list[dict], dict]:
    results: list[dict] = []
    counters = {
        "policy_violations": 0,
        "capacity_violations": 0,
        "accounting_failures": 0,
        "missed_escalations": 0,
    }

    for i in range(scenarios):
        reset_state()
        contains_nuts = rng.random() < 0.32
        refrigeration = rng.random() < 0.25
        sandwiches = rng.randint(5, 180)
        bread = rng.randint(0, 25)
        deadline = rng.choice(["19:30", "20:00", "20:30", "21:00"])

        event = engine.coordinate_rescue(
            donor_name=f"Synthetic Donor {i + 1}",
            sandwiches=sandwiches,
            bread_loaves=bread,
            pickup_deadline=deadline,
            contains_nuts=contains_nuts,
            requires_refrigeration=refrigeration,
        )

        recipient_by_id = {r["id"]: r for r in RECIPIENTS}
        allocated_ids = {a["recipient_id"] for a in event["allocation"]}
        rejected_ids = {r["id"] for r in event["rejected_recipients"]}

        no_rejected_allocated = not (allocated_ids & rejected_ids)
        capacity_ok = all(
            allocation["meals"] <= recipient_by_id[allocation["recipient_id"]]["capacity_meals"]
            for allocation in event["allocation"]
        )
        nut_policy_ok = all(
            not contains_nuts or recipient_by_id[rid]["accepts_nuts"]
            for rid in allocated_ids
        )
        refrigeration_ok = all(
            not refrigeration or recipient_by_id[rid]["refrigeration"]
            for rid in allocated_ids
        )
        accounting_ok = (
            sum(a["meals"] for a in event["allocation"]) + event["unallocated_meals"]
            == event["estimated_meals"]
        )
        escalation_ok = (event["unallocated_meals"] == 0) or event["human_approval_required"]

        if not (no_rejected_allocated and nut_policy_ok and refrigeration_ok):
            counters["policy_violations"] += 1
        if not capacity_ok:
            counters["capacity_violations"] += 1
        if not accounting_ok:
            counters["accounting_failures"] += 1
        if not escalation_ok:
            counters["missed_escalations"] += 1

        passed = all([
            no_rejected_allocated,
            capacity_ok,
            nut_policy_ok,
            refrigeration_ok,
            accounting_ok,
            escalation_ok,
        ])
        results.append({
            "scenario": i + 1,
            "passed": passed,
            "contains_nuts": contains_nuts,
            "requires_refrigeration": refrigeration,
            "estimated_meals": event["estimated_meals"],
            "unallocated_meals": event["unallocated_meals"],
            "human_escalation": event["human_approval_required"],
        })

    return results, counters


def _recovery_scenarios(scenarios: int = 50) -> dict:
    replacement_passed = 0
    escalation_passed = 0

    for i in range(scenarios):
        reset_state()
        event = engine.coordinate_rescue(
            donor_name=f"Recovery Donor {i + 1}",
            sandwiches=42,
            bread_loaves=18,
            pickup_deadline="20:30",
        )
        engine.cancel_assigned_volunteer(event["event_id"])
        recovered = engine.recover_logistics(event["event_id"])
        if (
            recovered.get("recovered") is True
            and recovered.get("method") == "replacement_volunteer"
            and recovered.get("volunteer", {}).get("id") == "VOL-2"
        ):
            replacement_passed += 1

        reset_state()
        event = engine.coordinate_rescue(
            donor_name=f"Escalation Donor {i + 1}",
            sandwiches=42,
            bread_loaves=18,
            pickup_deadline="20:30",
        )
        for volunteer in VOLUNTEERS:
            volunteer["available"] = False
        engine.cancel_assigned_volunteer(event["event_id"])
        escalated = engine.recover_logistics(event["event_id"])
        current = engine.get_event(event["event_id"])
        if (
            escalated.get("recovered") is False
            and escalated.get("human_approval_required") is True
            and current["status"] == "HUMAN_REVIEW"
        ):
            escalation_passed += 1

    return {
        "replacement_recovery_scenarios": scenarios,
        "replacement_recovery_passed": replacement_passed,
        "forced_escalation_scenarios": scenarios,
        "forced_escalation_passed": escalation_passed,
    }


def run_evaluation(seed: int = 42, scenarios: int = 500) -> dict:
    rng = random.Random(seed)
    results, counters = _safety_scenarios(rng, scenarios)
    recovery = _recovery_scenarios(50)

    passed_count = sum(1 for r in results if r["passed"])
    summary = {
        "seed": seed,
        "safety_scenarios": scenarios,
        "safety_passed": passed_count,
        "safety_failed": scenarios - passed_count,
        "safety_pass_rate": round(passed_count / scenarios, 4),
        "human_escalations": sum(1 for r in results if r["human_escalation"]),
        **counters,
        **recovery,
        "checks": [
            "never allocate to rejected recipient",
            "recipient capacity never exceeded",
            "nut allergen policy respected",
            "refrigeration requirements respected",
            "meal accounting conserved",
            "partial allocation always escalates",
            "volunteer cancellation recovers to backup when safe",
            "no-safe-logistics case escalates to a human",
        ],
        "results": results,
    }
    return summary


def main():
    summary = run_evaluation()
    out = Path(__file__).resolve().parents[1] / "evaluation" / "results.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        f"Safety evaluation: {summary['safety_passed']}/{summary['safety_scenarios']} scenarios passed"
    )
    print(
        "Recovery evaluation: "
        f"{summary['replacement_recovery_passed']}/{summary['replacement_recovery_scenarios']} backup recoveries; "
        f"{summary['forced_escalation_passed']}/{summary['forced_escalation_scenarios']} safe escalations"
    )
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
