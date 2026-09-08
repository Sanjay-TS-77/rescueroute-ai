import pytest


def test_strands_graph_builds_with_installed_sdk():
    pytest.importorskip("strands")
    from rescueroute.graph_workflow import rescue_graph, recovery_graph

    assert rescue_graph is not None
    assert recovery_graph is not None
    assert type(rescue_graph).__name__ == "Graph"
    assert type(recovery_graph).__name__ == "Graph"


def test_agentcore_entrypoint_imports_with_installed_sdk():
    pytest.importorskip("bedrock_agentcore")
    pytest.importorskip("strands")
    from rescueroute.agentcore_app import app

    assert app is not None
    assert type(app).__name__ == "BedrockAgentCoreApp"
