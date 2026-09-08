from __future__ import annotations
import json
from .agents import run_new_rescue
from .store import reset_state, snapshot

def main():
    reset_state()
    result = run_new_rescue(
        donor_name="ABC Bakery",
        sandwiches=42,
        bread_loaves=18,
        pickup_deadline="20:30",
        contains_nuts=False,
        requires_refrigeration=False,
    )
    print("\n=== AGENT RESULT ===")
    print(result)
    print("\n=== STATE SNAPSHOT ===")
    print(json.dumps(snapshot(), indent=2, default=str))

if __name__ == "__main__":
    main()
