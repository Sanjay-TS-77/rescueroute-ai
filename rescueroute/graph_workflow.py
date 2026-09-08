from __future__ import annotations

import os

from strands import Agent
from strands.multiagent import GraphBuilder

from .tools import (
    assign_best_volunteer,
    cancel_volunteer,
    create_rescue_event,
    evaluate_recipient_eligibility,
    notify_parties,
    optimize_allocation,
    recover_from_volunteer_cancellation,
)

MODEL_ID = os.getenv("RESCUEROUTE_MODEL", "global.anthropic.claude-sonnet-4-6")


def _agent(name: str, prompt: str, tools: list) -> Agent:
    return Agent(
        name=name,
        model=MODEL_ID,
        callback_handler=None,
        tools=tools,
        system_prompt=prompt,
    )


intake_agent = _agent(
    "intake_agent",
    """
You are RescueRoute Intake. Read the donation request and CREATE the rescue event using your tool.
Do not just summarize. Return the created event_id prominently so downstream graph nodes can act on it.
Never invent missing food quantities or safety flags.
""",
    [create_rescue_event],
)

safety_agent = _agent(
    "safety_agent",
    """
You are RescueRoute Safety. Find the event_id in the task/dependency context and CALL the eligibility tool.
Hard tool results are authoritative. Never override allergen, refrigeration, closing-time, or recipient policy rules.
Summarize eligible and rejected recipients, including rejection reasons.
""",
    [evaluate_recipient_eligibility],
)

matching_agent = _agent(
    "matching_agent",
    """
You are RescueRoute Matching. Find the event_id and CALL the allocation tool.
Respect eligibility and capacity exactly. Report allocation and any unallocated meals.
If the tool indicates human approval is required, say so explicitly.
""",
    [optimize_allocation],
)

logistics_agent = _agent(
    "logistics_agent",
    """
You are RescueRoute Logistics. Find the event_id and CALL the volunteer-assignment tool.
Do not claim a volunteer exists unless the tool assigned one. Report route distance and assignment status.
""",
    [assign_best_volunteer],
)

communications_agent = _agent(
    "communications_agent",
    """
You are RescueRoute Communications. Find the event_id and CALL the notification tool.
Only generate notifications for the plan already created by upstream nodes.
Return final coordination status and whether human action is still required.
""",
    [notify_parties],
)

failure_agent = _agent(
    "failure_injector",
    """
You are a demo failure injector. Find the event_id and CALL cancel_volunteer exactly once.
Return the cancellation result. Do not make any additional changes.
""",
    [cancel_volunteer],
)

recovery_agent = _agent(
    "recovery_agent",
    """
You are RescueRoute Recovery. Find the event_id and CALL the recovery tool.
Attempt safe autonomous recovery. If the tool escalates to a human, preserve that decision exactly.
""",
    [recover_from_volunteer_cancellation],
)


def build_rescue_graph():
    """Build the primary Strands Graph used for end-to-end rescue coordination."""
    builder = GraphBuilder()
    builder.add_node(intake_agent, "intake")
    builder.add_node(safety_agent, "safety")
    builder.add_node(matching_agent, "matching")
    builder.add_node(logistics_agent, "logistics")
    builder.add_node(communications_agent, "communications")
    builder.add_edge("intake", "safety")
    builder.add_edge("safety", "matching")
    builder.add_edge("matching", "logistics")
    builder.add_edge("logistics", "communications")
    builder.set_entry_point("intake")
    builder.set_execution_timeout(180)
    return builder.build()


def build_recovery_graph():
    """Build a failure -> autonomous-recovery Strands Graph for the demo."""
    builder = GraphBuilder()
    builder.add_node(failure_agent, "cancel")
    builder.add_node(recovery_agent, "recover")
    builder.add_edge("cancel", "recover")
    builder.set_entry_point("cancel")
    builder.set_execution_timeout(120)
    return builder.build()


rescue_graph = build_rescue_graph()
recovery_graph = build_recovery_graph()


def run_graph_rescue(task: str):
    return rescue_graph(task)


def run_graph_recovery(event_id: str):
    return recovery_graph(f"Simulate a volunteer cancellation and recover rescue event {event_id}.")
