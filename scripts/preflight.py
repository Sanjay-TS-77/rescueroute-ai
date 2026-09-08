from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "LICENSE",
    "DISCLOSURE.md",
    "Dockerfile",
    "main.py",
    "docs/architecture.svg",
    "docs/ARCHITECTURE.md",
    "docs/DEMO_SCRIPT.md",
    "docs/JUDGING.md",
    "docs/SECURITY.md",
    "evaluation/results.json",
    "submission/DEVPOST.md",
    "submission/CHECKLIST.md",
    "submission/BUILDER_POST_1.md",
    "submission/BUILDER_POST_2.md",
    "submission/BUILDER_POST_3.md",
]

missing = [path for path in REQUIRED if not (ROOT / path).exists()]
if missing:
    raise SystemExit("Missing required submission files: " + ", ".join(missing))

results = json.loads((ROOT / "evaluation/results.json").read_text(encoding="utf-8"))
checks = {
    "safety": results["safety_passed"] == results["safety_scenarios"],
    "replacement_recovery": (
        results["replacement_recovery_passed"] == results["replacement_recovery_scenarios"]
    ),
    "safe_escalation": (
        results["forced_escalation_passed"] == results["forced_escalation_scenarios"]
    ),
}
if not all(checks.values()):
    raise SystemExit(f"Evaluation quality gate failed: {checks}")

print(f"Preflight passed: {len(REQUIRED)} required files present")
print(
    "Evaluation evidence: "
    f"{results['safety_passed']}/{results['safety_scenarios']} safety, "
    f"{results['replacement_recovery_passed']}/{results['replacement_recovery_scenarios']} backup recovery, "
    f"{results['forced_escalation_passed']}/{results['forced_escalation_scenarios']} safe escalation"
)
