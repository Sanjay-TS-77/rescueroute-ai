# Agents for Humans: Where Autonomy Should Stop

The difficult part of building an autonomous agent is not deciding what the agent can do. It is deciding what the agent must **not** do without a person.

While building RescueRoute AI for the Agents for Humans Hackathon, I used a simple design principle: automate repetitive coordination aggressively, but never let free-form model reasoning weaken a hard safety constraint.

## Three layers of decision making

RescueRoute separates decisions into three layers.

### 1. Model reasoning

Strands agents interpret the donation, understand workflow context, and select actions. This is where flexible reasoning is useful.

### 2. Deterministic guardrails

Food-safety and operational invariants live in tools. Allergen policy, refrigeration, closing time, and recipient capacity are evaluated deterministically. Allocation cannot include a recipient that failed eligibility.

### 3. Human authority

When the system cannot complete a rescue while preserving those constraints, it does not invent an exception. It creates an explicit human-review state with a reason.

This means “human in the loop” is not implemented as a confirmation dialog after every agent step. That would simply move the repetitive work back to the user. Human attention is reserved for genuine ambiguity or risk.

## A concrete example

Imagine a donation contains nuts. One nearby shelter has a strict no-nut policy. RescueRoute excludes that shelter automatically.

If the remaining recipients have enough capacity, the agent continues without interrupting anyone. If safe capacity is insufficient, the remaining meals are left unallocated and a human decision is requested.

The model is never allowed to decide that the shelter’s policy is probably flexible.

## Failure recovery follows the same principle

When a volunteer cancels, RescueRoute first searches for a replacement. If none exists, it checks whether recipients are capable of self-pickup. If neither path is safe, the workflow escalates.

The point is not to maximize automation percentage. The point is to maximize **safe autonomous resolution**.

## Why this matters beyond food rescue

The same pattern applies to many agentic systems:

- a finance agent can prepare and reconcile but should escalate policy exceptions;
- an IT agent can remediate known incidents but escalate destructive changes;
- a healthcare operations agent can coordinate scheduling but preserve clinical authority;
- a procurement agent can execute routine purchases but surface spend-policy exceptions.

The best agent architecture is often a boundary architecture: flexible reasoning on one side, deterministic constraints and human authority on the other.
