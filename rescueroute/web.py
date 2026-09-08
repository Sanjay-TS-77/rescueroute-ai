from __future__ import annotations

import os
import importlib.util
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import engine
from .store import VOLUNTEERS, reset_state

app = FastAPI(
    title="RescueRoute AI",
    description="Autonomous food-rescue coordination powered by Strands Agents.",
    version="0.2.0",
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class RescueRequest(BaseModel):
    donor_name: str = Field(min_length=1, max_length=120)
    sandwiches: int = Field(ge=0, le=10000)
    bread_loaves: int = Field(ge=0, le=10000)
    pickup_deadline: str = Field(default="20:30", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    contains_nuts: bool = False
    requires_refrigeration: bool = False
    mode: Literal["deterministic", "strands"] = "deterministic"


class ApprovalRequest(BaseModel):
    note: str = Field(default="Approved by human operator", min_length=1, max_length=300)


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "rescueroute-ai",
        "strands_graph_available": importlib.util.find_spec("strands") is not None,
        "agentcore_sdk_available": importlib.util.find_spec("bedrock_agentcore") is not None,
    }


@app.post("/api/reset")
def reset_demo():
    reset_state()
    return {"ok": True}


@app.get("/api/rescues")
def rescues():
    return {"events": engine.list_events()}


@app.get("/api/rescues/{event_id}")
def rescue(event_id: str):
    try:
        return engine.get_event(event_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/rescues")
def create_rescue(payload: RescueRequest):
    values = payload.model_dump(exclude={"mode"})
    if payload.mode == "strands":
        try:
            from .graph_workflow import run_graph_rescue

            prompt = (
                "Coordinate this donation end-to-end: "
                f"donor={payload.donor_name}; sandwiches={payload.sandwiches}; "
                f"bread_loaves={payload.bread_loaves}; pickup_deadline={payload.pickup_deadline}; "
                f"contains_nuts={payload.contains_nuts}; "
                f"requires_refrigeration={payload.requires_refrigeration}."
            )
            run_graph_rescue(prompt)
            events = engine.list_events()
            if not events:
                raise RuntimeError("Strands graph completed without creating an event.")
            return events[-1]
        except Exception as exc:
            if os.getenv("RESCUEROUTE_STRANDS_FALLBACK", "false").lower() == "true":
                return engine.coordinate_rescue(**values)
            raise HTTPException(status_code=502, detail=f"Strands graph failed: {exc}") from exc

    try:
        return engine.coordinate_rescue(**values)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/rescues/{event_id}/cancel-volunteer")
def cancel_and_recover(event_id: str):
    try:
        cancelled = engine.cancel_assigned_volunteer(event_id)
        recovery = engine.recover_logistics(event_id)
        return {
            "cancelled": cancelled,
            "recovery": recovery,
            "event": engine.get_event(event_id),
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/demo/rescues/{event_id}/force-logistics-escalation")
def force_logistics_escalation(event_id: str):
    """Demo-only failure injection: exhaust volunteers and exercise the safe human-escalation path."""
    try:
        for volunteer in VOLUNTEERS:
            volunteer["available"] = False
        cancelled = engine.cancel_assigned_volunteer(event_id)
        recovery = engine.recover_logistics(event_id)
        return {
            "cancelled": cancelled,
            "recovery": recovery,
            "event": engine.get_event(event_id),
            "demo_only": True,
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/rescues/{event_id}/approve")
def approve(event_id: str, payload: ApprovalRequest):
    try:
        return {
            "approval": engine.approve_human_action(event_id, payload.note),
            "event": engine.get_event(event_id),
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
