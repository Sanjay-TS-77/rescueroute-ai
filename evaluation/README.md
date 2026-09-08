# RescueRoute evaluation methodology

The committed evaluation is intentionally deterministic and reproducible. It tests the **hard operational invariants** enforced by RescueRoute's action layer rather than asking an LLM to grade another LLM.

## Safety suite

`python -m rescueroute.evaluate` generates 500 seeded synthetic donations with randomized quantities, allergen flags, refrigeration requirements, and pickup deadlines. Each scenario checks:

- rejected recipients are never allocated food,
- recipient capacity is never exceeded,
- nut-allergen restrictions are respected,
- refrigeration requirements are respected,
- meal accounting is conserved exactly,
- any partial allocation is escalated to a human.

## Recovery suite

The same command also executes 50 volunteer-cancellation cases where a safe backup exists and 50 cases where all volunteer capacity is unavailable. It checks that RescueRoute:

- autonomously assigns the backup volunteer when safe, and
- escalates rather than inventing an unsafe logistics plan when no safe recovery exists.

The full machine-readable result is committed in `evaluation/results.json`.
