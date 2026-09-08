from __future__ import annotations

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from .graph_workflow import run_graph_rescue

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload):
    """AgentCore Runtime entrypoint for the RescueRoute Strands Graph."""
    prompt = payload.get("prompt") if isinstance(payload, dict) else None
    if not prompt:
        return {"error": "Provide a non-empty 'prompt' field."}

    result = run_graph_rescue(prompt)
    return {
        "status": str(getattr(result, "status", "completed")),
        "result": str(result),
    }


if __name__ == "__main__":
    app.run()
