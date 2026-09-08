# Judging Evidence Map

This document maps RescueRoute directly to the five equally weighted Agents for Humans criteria.

| Criterion | Evidence in repository |
|---|---|
| Technical Implementation | `graph_workflow.py` uses Strands Graph with five specialized agents; `tools.py` exposes real actions; `engine.py` enforces deterministic guardrails; `agentcore_app.py` is AgentCore Runtime-ready; CI and evaluation are included. |
| Design | `rescueroute/static/` is a complete command-center experience with rescue intake, execution timeline, live metrics, failure simulation, and human approval. |
| Potential Impact | The workflow targets repetitive coordination among food donors, community organizations, and volunteers rather than a generic chat task. |
| Creativity & Originality | The agent coordinates a multi-party community logistics workflow and stays quiet unless a safety/capacity/logistics decision requires a human. |
| Presentation | `DEMO_SCRIPT.md` is structured for a sub-five-minute end-to-end demonstration with normal operation, autonomous recovery, and safe escalation. |

## Quantitative evidence

Run:

```bash
python -m rescueroute.evaluate
```

The committed benchmark contains 500 seeded safety scenarios plus 50 backup-recovery and 50 forced-escalation scenarios. It checks eight invariants:

1. no rejected recipient is allocated food;
2. recipient capacity is never exceeded;
3. nut-allergen policies are respected;
4. refrigeration requirements are respected;
5. meal accounting is conserved;
6. incomplete allocation triggers human escalation;
7. a cancelled volunteer is replaced automatically when a safe backup exists;
8. no-safe-logistics cases escalate rather than hallucinating a route.

Current committed result: **500/500 safety**, **50/50 backup recovery**, **50/50 safe escalation**. See `evaluation/results.json`.
