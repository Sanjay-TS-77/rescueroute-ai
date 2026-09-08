# Agents for Humans: Building RescueRoute with Strands Agents

Community food rescue looks simple from a distance: one organization has surplus food and another organization needs it. The operational reality is a chain of repetitive decisions—what food is available, who can safely accept it, how much capacity each recipient has, who can pick it up, who needs to be notified, and what happens when the plan changes.

For the Agents for Humans Hackathon, I built **RescueRoute AI**, an autonomous coordination agent that handles that routine work while preserving a clear boundary for human judgment.

## Why I used a Strands Graph

I did not want a single general-purpose agent to own the entire workflow. The operational sequence matters, especially around food-safety constraints. RescueRoute therefore uses the Strands Graph pattern with five specialized stages:

`Intake -> Safety -> Matching -> Logistics -> Communications`

The intake agent creates the rescue event. The safety agent invokes eligibility checks. The matching agent allocates food only to eligible recipients. The logistics agent assigns transport. The communications agent produces stakeholder notifications only after a viable plan exists.

That structure is useful for more than code organization. It gives the workflow explicit checkpoints and makes execution understandable during debugging and judging.

## Keeping hard rules outside the model

The most important architectural decision was to avoid asking the language model to decide whether a safety policy could be ignored.

RescueRoute uses deterministic Strands tools for hard rules. A recipient is excluded when an allergen conflicts with policy, refrigeration is required but unavailable, or closing time makes the pickup infeasible. Allocation is capacity-bound. When safe recipient capacity is insufficient, the tool sets a human-review state instead of allowing the model to trade safety for completion.

This creates a useful division of labor:

- the model interprets context and orchestrates actions;
- deterministic tools enforce invariants;
- humans resolve situations where no safe automatic answer exists.

## Designing for failure, not just the happy path

A food rescue workflow is only useful if it survives operational change. The demo includes a volunteer cancellation after the initial plan has been coordinated.

Instead of immediately paging a human, RescueRoute attempts a replacement volunteer. If that is not possible, it checks whether all allocated recipients can self-pickup. Only when no safe recovery remains does the workflow escalate.

That behavior is central to the Agents for Humans theme: the agent should absorb routine disruption instead of creating another notification for a person to manage.

## Evidence, not just a demo

I also added a seeded 500-scenario safety benchmark plus 100 recovery scenarios. It checks that rejected recipients are never allocated food, capacity is not exceeded, allergen and refrigeration rules hold, meal accounting is conserved, and incomplete allocation always escalates.

The current benchmark passes 500/500 safety scenarios, 50/50 backup recoveries, and 50/50 forced safe escalations.

The next step is deploying the same Strands Graph through Amazon Bedrock AgentCore Runtime and adding production persistence and observability.
