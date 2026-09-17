import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_mcp_tools():
    response = client.get("/api/v1/mcp/tools")
    assert response.status_code == 200
    tools = response.json()
    assert isinstance(tools, list)
    tool_names = [t["name"] for t in tools]
    assert "clickstack_sql" in tool_names
    assert "clickstack_timeseries" in tool_names
    assert "clickstack_search" in tool_names
    assert "clickstack_trace_waterfall" in tool_names


@patch("app.telemetry.client.clickhouse_client.execute_query", new_callable=AsyncMock)
def test_execute_mcp_sql_tool(mock_execute):
    mock_execute.return_value = {"data": [{"result": 1}], "rows": 1}

    response = client.post(
        "/api/v1/mcp/execute",
        json={
            "tool_name": "clickstack_sql",
            "arguments": {"query": "SELECT 1"},
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["tool_name"] == "clickstack_sql"
    assert res["result"] == {"data": [{"result": 1}], "rows": 1}
    mock_execute.assert_called_once_with("SELECT 1")


def test_execute_unknown_mcp_tool():
    response = client.post(
        "/api/v1/mcp/execute",
        json={
            "tool_name": "unknown_tool",
            "arguments": {},
        },
    )
    assert response.status_code == 404
    assert "Unknown MCP tool" in response.json()["detail"]


def test_execute_prohibited_sql_via_mcp():
    response = client.post(
        "/api/v1/mcp/execute",
        json={
            "tool_name": "clickstack_sql",
            "arguments": {"query": "DROP TABLE telemetry.otel_logs"},
        },
    )
    assert response.status_code == 400
    assert "Security violation" in response.json()["detail"]
