# SDK and deployment verification notes

RescueRoute deliberately separates **offline-verifiable operational safety** from **AWS-dependent agent execution**.

## Offline-verifiable path

The deterministic engine, FastAPI product flow, failure recovery, human escalation, unit/API tests, and synthetic benchmark run without AWS credentials. This lets a reviewer verify that the hard constraints are real and are not prompt-only claims.

## Strands path

`rescueroute/graph_workflow.py` uses `GraphBuilder` from `strands.multiagent`. Current Strands documentation describes Graph as deterministic dependency-based orchestration where output from one node is propagated to connected nodes. The project includes an SDK integration test that constructs both RescueRoute graphs when the dependency is installed.

Official reference: https://strandsagents.com/docs/api/python/strands.multiagent.graph/

The configured Bedrock model is `global.anthropic.claude-sonnet-4-6`, which is the current Strands Python default and a valid Amazon Bedrock global inference ID.

Official references:

- https://strandsagents.com/docs/user-guide/quickstart/python/
- https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-sonnet-4-6.html

## AgentCore path

`main.py` and `rescueroute/agentcore_app.py` use `BedrockAgentCoreApp` and `@app.entrypoint`, matching the current AgentCore Runtime Python integration contract.

Official reference: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/using-any-agent-framework.html

The current AgentCore CLI is distributed through npm and supports Python + Strands + Bedrock projects using CodeZip deployments.

Official reference: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-get-started-cli.html
