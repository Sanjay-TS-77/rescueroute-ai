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


@app.entrypoint
def invoke(payload):
    """AgentCore Runtime entrypoint for RescueRoute's Strands graph.

    During new-account Bedrock verification, a structured request remains usable
    through the deterministic safety engine and DynamoDB. That fallback is only
    activated for AWS's explicit account-verification error; other failures stay
    visible so implementation bugs cannot be silently hidden.
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
        message = str(exc)
        verification_pending = "account is currently being verified" in message.lower()
        if not verification_pending or structured is None:
            raise

        event = engine.coordinate_rescue(**structured)
        return {
            "status": event["status"],
            "event": event,
            "execution_mode": "deterministic-bedrock-verification-fallback",
            "runtime": "amazon-bedrock-agentcore",
            "state_backend": "dynamodb" if using_dynamodb() else "memory",
            "bedrock_status": "account_verification_pending",
        }


if __name__ == "__main__":
    app.run()
