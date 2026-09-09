from __future__ import annotations

from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from . import engine
from .graph_workflow import run_graph_rescue
from .store import using_dynamodb

app = BedrockAgentCoreApp()


def _structured_request(payload: dict[str, Any]) -> dict[str, Any] | None:
    required = {"donor_name", "sandwiches", "bread_loaves", "pickup_deadline"}
    if not required.issubset(payload):
        return None
    return {
        "donor_name": str(payload["donor_name"]),
        "sandwiches": int(payload["sandwiches"]),
        "bread_loaves": int(payload["bread_loaves"]),
        "pickup_deadline": str(payload["pickup_deadline"]),
        "contains_nuts": bool(payload.get("contains_nuts", False)),
        "requires_refrigeration": bool(payload.get("requires_refrigeration", False)),
    }


def _bedrock_temporarily_unavailable(message: str) -> bool:
    text = message.lower()
    return any(marker in text for marker in (
        "account is currently being verified",
        "operation not allowed",
    ))


@app.entrypoint
def invoke(payload):
    """AgentCore Runtime entrypoint for RescueRoute's Strands graph.

    During AWS account verification/entitlement activation, a structured request
    remains usable through the deterministic safety engine and DynamoDB. Only
    explicit Bedrock account-level restriction messages activate the fallback;
    implementation errors stay visible.
    """
    if not isinstance(payload, dict):
        return {"error": "Payload must be a JSON object."}

    prompt = payload.get("prompt")
    structured = _structured_request(payload)
    if not prompt and structured:
        prompt = (
            "Coordinate this donation end-to-end using tools: "
            f"donor_name={structured['donor_name']}; "
            f"sandwiches={structured['sandwiches']}; "
            f"bread_loaves={structured['bread_loaves']}; "
            f"pickup_deadline={structured['pickup_deadline']}; "
            f"contains_nuts={structured['contains_nuts']}; "
            f"requires_refrigeration={structured['requires_refrigeration']}."
        )
    if not prompt:
        return {
            "error": (
                "Provide a non-empty 'prompt' or structured donor_name, sandwiches, "
                "bread_loaves and pickup_deadline fields."
            )
        }

    try:
        result = run_graph_rescue(str(prompt))
        return {
            "status": str(getattr(result, "status", "completed")),
            "result": str(result),
            "execution_mode": "strands-bedrock",
            "runtime": "amazon-bedrock-agentcore",
            "state_backend": "dynamodb" if using_dynamodb() else "memory",
        }
    except Exception as exc:
        if not _bedrock_temporarily_unavailable(str(exc)) or structured is None:
            raise

        event = engine.coordinate_rescue(**structured)
        return {
            "status": event["status"],
            "event": event,
            "execution_mode": "deterministic-bedrock-verification-fallback",
            "runtime": "amazon-bedrock-agentcore",
            "state_backend": "dynamodb" if using_dynamodb() else "memory",
            "bedrock_status": "account_verification_or_entitlement_pending",
        }


if __name__ == "__main__":
    app.run()
