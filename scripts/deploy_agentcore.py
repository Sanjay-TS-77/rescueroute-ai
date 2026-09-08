from __future__ import annotations

import json
import os
import sys
import time
import uuid

import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_REGION", "us-west-2")
BUCKET = os.environ["AGENTCORE_ARTIFACT_BUCKET"]
OBJECT_KEY = os.environ["AGENTCORE_ARTIFACT_KEY"]
RUNTIME_NAME = os.environ.get("AGENTCORE_RUNTIME_NAME", "RescueRouteAI")
RUNTIME_ROLE_ARN = os.environ["AGENTCORE_RUNTIME_ROLE_ARN"]
MODEL_ID = os.environ.get("RESCUEROUTE_MODEL", "global.anthropic.claude-sonnet-4-6")

control = boto3.client("bedrock-agentcore-control", region_name=REGION)
runtime = boto3.client("bedrock-agentcore", region_name=REGION)


def artifact() -> dict:
    return {
        "codeConfiguration": {
            "code": {"s3": {"bucket": BUCKET, "prefix": OBJECT_KEY}},
            "runtime": "PYTHON_3_13",
            "entryPoint": ["main.py"],
        }
    }


def find_runtime() -> dict | None:
    paginator = control.get_paginator("list_agent_runtimes")
    for page in paginator.paginate():
        for item in page.get("agentRuntimes", []):
            if item.get("agentRuntimeName") == RUNTIME_NAME:
                return item
    return None


def create_or_update() -> tuple[str, str]:
    existing = find_runtime()
    common = {
        "agentRuntimeArtifact": artifact(),
        "roleArn": RUNTIME_ROLE_ARN,
        "networkConfiguration": {"networkMode": "PUBLIC"},
        "description": "RescueRoute AI autonomous food-rescue coordinator built with Strands Agents",
        "environmentVariables": {
            "AWS_REGION": REGION,
            "RESCUEROUTE_MODEL": MODEL_ID,
        },
        "lifecycleConfiguration": {
            "idleRuntimeSessionTimeout": 300,
            "maxLifetime": 1800,
        },
    }

    if existing:
        runtime_id = existing["agentRuntimeId"]
        print(f"Updating AgentCore runtime {runtime_id} ...")
        response = control.update_agent_runtime(agentRuntimeId=runtime_id, **common)
    else:
        print(f"Creating AgentCore runtime {RUNTIME_NAME} ...")
        response = control.create_agent_runtime(agentRuntimeName=RUNTIME_NAME, **common)

    return response["agentRuntimeId"], response["agentRuntimeArn"]


def wait_ready(runtime_id: str, timeout: int = 1200) -> dict:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        state = control.get_agent_runtime(agentRuntimeId=runtime_id)
        status = state.get("status")
        if status != last:
            print(f"Runtime status: {status}")
            last = status
        if status in {"READY", "FAILED"}:
            return state
        time.sleep(15)
    raise TimeoutError(f"AgentCore runtime did not become ready within {timeout}s")


def smoke_invoke(runtime_arn: str) -> None:
    prompt = (
        "Coordinate a rescue from ABC Bakery: 42 sandwiches, 18 bread loaves, "
        "pickup before 20:30, no nuts, no refrigeration. End with the rescue status."
    )
    try:
        response = runtime.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn,
            qualifier="DEFAULT",
            runtimeSessionId=str(uuid.uuid4()),
            payload=json.dumps({"prompt": prompt}).encode("utf-8"),
        )
        body = response["response"].read().decode("utf-8")
        print("LIVE_AGENTCORE_RESPONSE_START")
        print(body)
        print("LIVE_AGENTCORE_RESPONSE_END")
    except ClientError as exc:
        message = str(exc)
        # A brand-new AWS account can temporarily block Bedrock inference while
        # account verification completes. Deployment itself is still valid.
        if "currently being verified" in message:
            print("BEDROCK_ACCOUNT_VERIFICATION_PENDING")
            print(message)
            return
        raise


def main() -> int:
    runtime_id, runtime_arn = create_or_update()
    state = wait_ready(runtime_id)
    print(json.dumps({
        "agentRuntimeId": runtime_id,
        "agentRuntimeArn": runtime_arn,
        "status": state.get("status"),
    }, indent=2))
    if state.get("status") != "READY":
        print(json.dumps(state, default=str, indent=2))
        return 1
    smoke_invoke(runtime_arn)
    return 0


if __name__ == "__main__":
    sys.exit(main())
