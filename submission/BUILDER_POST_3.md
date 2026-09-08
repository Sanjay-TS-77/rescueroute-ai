# Agents for Humans: From Strands Prototype to AgentCore-Ready Architecture

A hackathon agent can be impressive in a notebook and still be difficult to operate as a real service. For RescueRoute AI, I wanted the local Strands workflow and the deployment architecture to share the same core instead of creating a separate “demo path” and “production path.”

## One graph, two execution surfaces

The main RescueRoute workflow lives in `graph_workflow.py` as a Strands Graph. Locally, it can be invoked directly from Python or through the FastAPI command center. For AWS deployment, the same graph is wrapped by `BedrockAgentCoreApp`.

The AgentCore entrypoint is intentionally thin: it receives a prompt, invokes the graph, and returns the result. Operational logic remains in the Strands agents and tools.

That separation reduces deployment-specific coupling and makes it easier to test the workflow independently.

## Why AgentCore fits this workload

Food-rescue coordination is naturally an agent runtime problem rather than a single synchronous completion. The workflow has multiple stages, tool calls, recoverable failures, and a need for operational visibility.

AgentCore Runtime provides a deployment target designed for agent workloads, while Strands provides the agent loop and graph orchestration inside the application.

For the hackathon build, the repository includes an AgentCore-compatible Python entrypoint. The next production steps are persistence, identity, and observability.

## Observability is part of trust

An autonomous system should be able to answer “what did you do?” RescueRoute therefore records a structured audit trail for state-changing actions such as:

- event creation;
- eligibility evaluation;
- allocation;
- volunteer assignment;
- notification generation;
- volunteer cancellation;
- autonomous recovery;
- human escalation and approval.

The command-center demo renders that audit trail as an execution timeline. In an AgentCore deployment, the next step is exporting traces through the supported observability stack so model/tool execution and business-state events can be correlated.

## Test the invariants separately from the model

One deployment lesson is that model evaluation and business-rule evaluation are different problems. RescueRoute includes a deterministic 500-scenario safety benchmark plus 100 recovery scenarios for hard invariants so failures in capacity, allergen, refrigeration, accounting, or escalation logic can be caught without invoking a model.

This keeps CI fast and creates a stable safety baseline while the prompts and model behavior evolve.

## The architecture principle

The emerging pattern is simple:

**Strands for reasoning and orchestration. AgentCore for agent runtime. Deterministic tools for policy. Observability for trust. Humans for true judgment.**

That is the architecture I would keep as RescueRoute moves from hackathon demo to a real community operations service.
