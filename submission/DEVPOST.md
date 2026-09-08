# RescueRoute AI — Devpost Submission Draft

## Tagline

Autonomous food-rescue coordination that handles the routine work and surfaces humans only when judgment matters.

## Track

**Good Neighbor Agents**

## Inspiration

Food rescue is often treated as a supply problem, but many local organizations face a coordination problem: a donor has surplus food, several organizations may need it, each recipient has different capacity and safety constraints, a volunteer may or may not be available, and every operational change creates another round of calls and messages.

A human coordinator can spend scarce time checking the same constraints and relaying the same updates. RescueRoute was built around a simple question: what if the routine coordination happened autonomously, while human attention was reserved for the decisions that actually require judgment?

## What it does

A donor submits a surplus-food event. RescueRoute then:

1. creates a structured rescue event;
2. checks recipient eligibility against allergen, refrigeration, opening-time, and policy constraints;
3. allocates estimated meals under recipient capacity limits;
4. assigns available volunteer logistics;
5. prepares notifications for donor, recipients, and volunteer;
6. records every operational action in an audit timeline;
7. responds to a volunteer cancellation by attempting a safe autonomous recovery;
8. escalates to a human only when no safe automatic path remains.

The result is not another assistant that tells a coordinator what to do. RescueRoute performs the coordination work.

## How we built it

The main workflow is implemented with the **Strands Agents SDK Graph pattern**. Five specialized Strands agents form an explicit sequence:

`Intake -> Safety -> Matching -> Logistics -> Communications`

Each agent is given a narrow responsibility and action tools. The graph structure prevents the workflow from casually skipping required stages.

Hard operational rules are intentionally separated from free-form model reasoning. Deterministic Python tools enforce recipient eligibility, allergen restrictions, refrigeration requirements, closing-time constraints, capacity, and human-escalation conditions. The model decides which action to take; the tools decide whether the action is allowed.

A second recovery path handles volunteer cancellation. The system first attempts a replacement volunteer, then considers recipient self-pickup when safe, and only then asks for human logistics coordination.

The project includes an **Amazon Bedrock AgentCore Runtime-compatible** entrypoint using `BedrockAgentCoreApp`, with Amazon Bedrock / Claude Sonnet 4.6 as the configured Strands model.

For product experience, RescueRoute includes a FastAPI command center showing intake, routing metrics, an execution timeline, failure simulation, and human approval.

## Testing and evaluation

We created a seeded benchmark with 500 deterministic safety scenarios plus 100 failure-recovery scenarios. It validates:

- rejected recipients are never allocated food;
- capacity is never exceeded;
- nut-allergen policy is respected;
- refrigeration requirements are respected;
- meal accounting is conserved;
- incomplete safe allocation always triggers human escalation;
- a cancelled volunteer moves to a safe backup when one exists;
- no-safe-logistics cases escalate instead of inventing a plan.

Current result: **500/500 safety scenarios, 50/50 backup recoveries, and 50/50 forced safe escalations passed**.

The automated test suite additionally covers normal coordination, safety exclusions, partial allocation, autonomous backup-volunteer recovery, and escalation when no safe recovery remains.

## Challenges we ran into

The hardest design decision was deciding where autonomy should end. A naive multi-agent system can make an impressive demo while still allowing model reasoning to override operational constraints. We chose a hybrid architecture: Strands agents handle interpretation and orchestration, while deterministic tools own hard safety and capacity rules.

A second challenge was failure behavior. Real logistics workflows do not end when the first plan changes. RescueRoute therefore treats cancellation as a new operational event and attempts recovery instead of simply notifying a human.

## Accomplishments we’re proud of

- A real Strands Graph rather than a single chat loop.
- Deterministic safety boundaries around model reasoning.
- Autonomous recovery from a simulated volunteer cancellation.
- Explicit human escalation when safe autonomy ends.
- 500/500 seeded safety scenarios, 50/50 backup recoveries, and 50/50 safe escalations passing.
- A complete command-center experience rather than a CLI-only proof of concept.
- AgentCore Runtime-compatible deployment entrypoint.

## What we learned

The most useful agentic systems are not necessarily the systems with the most agents. They are systems with a clear boundary between model judgment, deterministic policy, external action, and human authority.

The Strands Graph pattern made those responsibilities visible in code and gave the project a workflow structure that mirrors how community operations actually happen.

## What’s next

The demo uses synthetic organizations and an in-memory operational store. A production version would add:

- DynamoDB persistence and idempotent writes;
- real donor/recipient onboarding;
- routing and mapping integration;
- SMS/email/WhatsApp notification providers;
- AgentCore Identity/IAM authorization;
- AgentCore/OpenTelemetry operational traces;
- recipient availability and inventory synchronization;
- organization-level analytics such as rescued weight, volunteer reliability, and coordination time saved.

The longer-term goal is broader than food donation: a reusable community logistics agent for local organizations coordinating scarce people, time, inventory, and transport.
