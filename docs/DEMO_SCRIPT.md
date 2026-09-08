# 5-minute Demo Script

## 0:00–0:25 — Problem

“Surplus food exists. Community need exists. The missing layer is often coordination: who can safely accept what, who can pick it up, how much each location can take, and what happens when plans fail.”

## 0:25–0:45 — What RescueRoute does

“RescueRoute is a Good Neighbor Agent built with Strands Agents. It coordinates a food rescue end-to-end and only surfaces when a human decision is actually needed.”

Show the architecture diagram for no more than 15 seconds.

## 0:45–2:10 — Normal rescue

Use the command center with:

- ABC Bakery
- 42 sandwiches
- 18 bread loaves
- pickup 20:30
- no allergen flag

Click **Coordinate rescue**.

Call out the execution timeline:

1. donation event created;
2. food-safety and recipient-policy checks applied;
3. eligible capacity allocated;
4. volunteer assigned;
5. notifications generated.

Point to **114 meals routed**, recipient count, zero human actions, and the final coordinated status.

## 2:10–3:05 — Autonomous recovery

Click **Cancel volunteer → auto-recover**.

Explain: “The agent does not ping an operator just because something changed. It first attempts a safe recovery.”

Show the audit trail recording the cancellation and replacement-volunteer recovery.

## 3:05–4:00 — Safety-driven human escalation

First click the **Allergen guardrail** preset and coordinate it. Point out that the nut-restricted shelter is excluded before allocation.

Then return to a standard rescue and click **Exhaust logistics → human decision**. This is a deliberate demo-only failure injection that makes every volunteer unavailable. RescueRoute refuses to invent a route and displays **Human decision required**.

This is the key message: autonomy ends where human judgment or unsafe tradeoffs begin.

## 4:00–4:30 — Technical proof

Show:

- `graph_workflow.py`: Strands Graph nodes and edges;
- `engine.py`: deterministic constraints;
- `evaluation/results.json`: 500/500 safety + 50/50 recovery + 50/50 safe escalation;
- AgentCore entrypoint.

## 4:30–4:55 — Close

“Most AI assistants tell people what to do. RescueRoute does the coordination, recovers from routine failures, and asks for attention only when judgment matters. That gives food donors and community organizations back the scarce resource they cannot replenish: people’s time.”

End on the RescueRoute command center.
