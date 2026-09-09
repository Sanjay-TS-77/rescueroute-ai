from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

from rescueroute import engine
from rescueroute.store import VOLUNTEERS, reset_state, using_dynamodb

STATIC_DIR = Path(__file__).parent / "rescueroute" / "static"


def _response(status: int, body: Any, content_type: str = "application/json", *, binary: bool = False):
    if content_type == "application/json" and not isinstance(body, str):
        body = json.dumps(body, separators=(",", ":"), default=str)
    return {
        "statusCode": status,
        "headers": {
            "content-type": content_type,
            "cache-control": "no-store" if content_type == "application/json" else "public, max-age=300",
            "x-content-type-options": "nosniff",
        },
        "isBase64Encoded": binary,
        "body": body,
    }


def _json_body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    return json.loads(raw)


def _structured(payload: dict[str, Any]) -> dict[str, Any]:
    required = ("donor_name", "sandwiches", "bread_loaves", "pickup_deadline")
    missing = [name for name in required if name not in payload]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    return {
        "donor_name": str(payload["donor_name"]),
        "sandwiches": int(payload["sandwiches"]),
        "bread_loaves": int(payload["bread_loaves"]),
        "pickup_deadline": str(payload["pickup_deadline"]),
        "contains_nuts": bool(payload.get("contains_nuts", False)),
        "requires_refrigeration": bool(payload.get("requires_refrigeration", False)),
    }


def _coordinate(payload: dict[str, Any]):
    values = _structured(payload)
    mode = str(payload.get("mode", "strands")).lower()
    if mode != "strands":
        event = engine.coordinate_rescue(**values)
        event["execution_mode"] = "deterministic-aws"
        return event

    prompt = (
        "Coordinate this donation end-to-end using your tools: "
        f"donor={values['donor_name']}; sandwiches={values['sandwiches']}; "
        f"bread_loaves={values['bread_loaves']}; pickup_deadline={values['pickup_deadline']}; "
        f"contains_nuts={values['contains_nuts']}; requires_refrigeration={values['requires_refrigeration']}."
    )
    try:
        from rescueroute.graph_workflow import run_graph_rescue
        run_graph_rescue(prompt)
        events = engine.list_events()
        if not events:
            raise RuntimeError("Strands graph completed without creating an event")
        event = events[-1]
        event["execution_mode"] = "strands-bedrock"
        return event
    except Exception as exc:
        message = str(exc).lower()
        if "account is currently being verified" not in message:
            raise
        event = engine.coordinate_rescue(**values)
        event["execution_mode"] = "deterministic-bedrock-verification-fallback"
        event["bedrock_status"] = "account_verification_pending"
        return event


def lambda_handler(event, context):
    try:
        request_context = event.get("requestContext", {}) if isinstance(event, dict) else {}
        http = request_context.get("http", {})
        method = http.get("method", "POST").upper()
        path = event.get("rawPath") or "/api/rescues"

        if method == "GET" and path == "/":
            return _response(200, (STATIC_DIR / "index.html").read_text(), "text/html; charset=utf-8")
        if method == "GET" and path == "/static/styles.css":
            return _response(200, (STATIC_DIR / "styles.css").read_text(), "text/css; charset=utf-8")
        if method == "GET" and path == "/static/app.js":
            return _response(200, (STATIC_DIR / "app.js").read_text(), "application/javascript; charset=utf-8")
        if method == "GET" and path in {"/health", "/api/health"}:
            return _response(200, {
                "ok": True,
                "service": "rescueroute-ai",
                "hosting": "aws-lambda-function-url",
                "region": os.getenv("AWS_REGION"),
                "state_backend": "dynamodb" if using_dynamodb() else "memory",
                "bedrock_model": os.getenv("RESCUEROUTE_MODEL"),
            })
        if method == "GET" and path == "/api/rescues":
            return _response(200, {"events": engine.list_events()})
        if method == "POST" and path == "/api/reset":
            reset_state()
            return _response(200, {"ok": True})
        if method == "POST" and path == "/api/rescues":
            return _response(200, _coordinate(_json_body(event)))

        if path.startswith("/api/rescues/"):
            parts = path.strip("/").split("/")
            if len(parts) >= 3:
                event_id = parts[2]
                if method == "GET" and len(parts) == 3:
                    return _response(200, engine.get_event(event_id))
                if method == "POST" and len(parts) == 4 and parts[3] == "cancel-volunteer":
                    cancelled = engine.cancel_assigned_volunteer(event_id)
                    recovery = engine.recover_logistics(event_id)
                    return _response(200, {"cancelled": cancelled, "recovery": recovery, "event": engine.get_event(event_id)})
                if method == "POST" and len(parts) == 4 and parts[3] == "approve":
                    payload = _json_body(event)
                    approval = engine.approve_human_action(event_id, str(payload.get("note", "Approved by human operator")))
                    return _response(200, {"approval": approval, "event": engine.get_event(event_id)})

        prefix = "/api/demo/rescues/"
        suffix = "/force-logistics-escalation"
        if method == "POST" and path.startswith(prefix) and path.endswith(suffix):
            event_id = path[len(prefix):-len(suffix)]
            for volunteer in VOLUNTEERS:
                volunteer["available"] = False
            cancelled = engine.cancel_assigned_volunteer(event_id)
            recovery = engine.recover_logistics(event_id)
            return _response(200, {"cancelled": cancelled, "recovery": recovery, "event": engine.get_event(event_id), "demo_only": True})

        return _response(404, {"detail": f"Route not found: {method} {path}"})
    except ValueError as exc:
        return _response(400, {"detail": str(exc)})
    except Exception as exc:
        return _response(500, {"detail": f"RescueRoute request failed: {exc}"})
