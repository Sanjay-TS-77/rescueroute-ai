from __future__ import annotations

import os
import signal
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from .graph_workflow import run_graph_recovery, run_graph_rescue
from .store import using_dynamodb

app = FastAPI(
    title="RescueRoute AI AgentCore Runtime",
    description="AWS-native Strands multi-agent food rescue coordinator.",
    version="1.0.0",
)


class InvocationRequest(BaseModel):
    prompt: str | None = Field(default=None, max_length=8000)
    input: dict[str, Any] | None = None
    action: Literal["coordinate", "recover"] = "coordinate"
    event_id: str | None = Field(default=None, max_length=64)

    def resolved_prompt(self) -> str:
        if self.prompt and self.prompt.strip():
            return self.prompt.strip()
        if self.input:
            value = self.input.get("prompt")
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/ping")
async def ping():
    return {
        "status": "Healthy",
        "service": "rescueroute-ai",
        "runtime_id": os.getenv("RUNTIME_ID", "local"),
        "state_backend": "dynamodb" if using_dynamodb() else "memory",
    }


@app.get("/health")
async def health():
    # Kept for local/container diagnostics in addition to AgentCore's required /ping.
    return await ping()


@app.post("/invocations")
async def invocations(payload: InvocationRequest):
    try:
        if payload.action == "recover":
            if not payload.event_id:
                raise HTTPException(status_code=400, detail="event_id is required for recovery")
            result = run_graph_recovery(payload.event_id)
        else:
            prompt = payload.resolved_prompt()
            if not prompt:
                raise HTTPException(status_code=400, detail="Provide a non-empty prompt")
            result = run_graph_rescue(prompt)

        return {
            "status": str(getattr(result, "status", "completed")),
            "action": payload.action,
            "event_id": payload.event_id,
            "result": str(result),
            "runtime": "amazon-bedrock-agentcore",
            "state_backend": "dynamodb" if using_dynamodb() else "memory",
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        # Do not echo credentials or environment data. The exception text is useful
        # for the hackathon smoke test and is also captured by AgentCore/CloudWatch.
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {exc}") from exc


def _shutdown(_sig, _frame):
    raise SystemExit(0)


signal.signal(signal.SIGTERM, _shutdown)
