from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List

from app.mcp.schemas import (
    MCPToolDefinition,
    MCPToolExecutionRequest,
    MCPToolExecutionResponse,
    MCPToolParameter,
)
from app.telemetry.client import clickhouse_client

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])

AVAILABLE_MCP_TOOLS: List[MCPToolDefinition] = [
    MCPToolDefinition(
        name="clickstack_sql",
        description="Execute a read-only SQL query against ClickHouse telemetry store (logs, metrics, traces).",
        parameters=[
            MCPToolParameter(
                name="query",
                type="string",
                description="Read-only SQL query starting with SELECT, SHOW, DESCRIBE, EXPLAIN.",
                required=True,
            )
        ],
    ),
    MCPToolDefinition(
        name="clickstack_timeseries",
        description="Fetch metric time-series data for a specific service or metric name.",
        parameters=[
            MCPToolParameter(
                name="metric_name",
                type="string",
                description="Metric name to filter (e.g. requests_total, requests_total_rust).",
                required=False,
            ),
            MCPToolParameter(
                name="service_name",
                type="string",
                description="Service name to filter (e.g. python-generator, rust-generator).",
                required=False,
            ),
            MCPToolParameter(
                name="limit",
                type="integer",
                description="Maximum number of data points to return.",
                required=False,
            ),
        ],
    ),
    MCPToolDefinition(
        name="clickstack_search",
        description="Search telemetry records (logs, traces, metrics) by text query or service name.",
        parameters=[
            MCPToolParameter(
                name="service_name",
                type="string",
                description="Service name to search.",
                required=False,
            ),
            MCPToolParameter(
                name="query_text",
                type="string",
                description="Search string or pattern.",
                required=False,
            ),
        ],
    ),
    MCPToolDefinition(
        name="clickstack_trace_waterfall",
        description="Get full distributed trace waterfall for a given trace ID.",
        parameters=[
            MCPToolParameter(
                name="trace_id",
                type="string",
                description="Trace ID hex string.",
                required=True,
            )
        ],
    ),
]


@router.get("/tools", response_model=List[MCPToolDefinition])
async def list_mcp_tools():
    return AVAILABLE_MCP_TOOLS


@router.post("/execute", response_model=MCPToolExecutionResponse)
async def execute_mcp_tool(body: MCPToolExecutionRequest):
    tool_name = body.tool_name
    args = body.arguments

    try:
        if tool_name == "clickstack_sql":
            query = args.get("query")
            if not query:
                raise HTTPException(status_code=400, detail="Missing required argument 'query'")
            result = await clickhouse_client.execute_query(query)
            return MCPToolExecutionResponse(tool_name=tool_name, status="success", result=result)

        elif tool_name == "clickstack_timeseries":
            metric_name = args.get("metric_name")
            service_name = args.get("service_name")
            limit = int(args.get("limit", 50))
            where_clauses = []
            if metric_name:
                where_clauses.append(f"MetricName = '{metric_name}'")
            if service_name:
                where_clauses.append(f"ServiceName = '{service_name}'")
            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            sql = f"SELECT MetricName, Value, ServiceName, TimeUnix FROM telemetry.otel_metrics_sum {where_str} ORDER BY TimeUnix DESC LIMIT {limit}"
            result = await clickhouse_client.execute_query(sql)
            return MCPToolExecutionResponse(tool_name=tool_name, status="success", result=result)

        elif tool_name == "clickstack_search":
            service_name = args.get("service_name")
            limit = int(args.get("limit", 50))
            where_clauses = []
            if service_name:
                where_clauses.append(f"ServiceName = '{service_name}'")
            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            sql = f"SELECT Timestamp, ServiceName, Body, SeverityText FROM telemetry.otel_logs {where_str} ORDER BY Timestamp DESC LIMIT {limit}"
            result = await clickhouse_client.execute_query(sql)
            return MCPToolExecutionResponse(tool_name=tool_name, status="success", result=result)

        elif tool_name == "clickstack_trace_waterfall":
            trace_id = args.get("trace_id")
            if not trace_id:
                raise HTTPException(status_code=400, detail="Missing required argument 'trace_id'")
            sql = f"SELECT ServiceName, SpanName, TraceId, SpanId, ParentSpanId, Duration, Timestamp FROM telemetry.otel_traces WHERE TraceId = '{trace_id}' ORDER BY Timestamp ASC"
            result = await clickhouse_client.execute_query(sql)
            return MCPToolExecutionResponse(tool_name=tool_name, status="success", result=result)

        else:
            raise HTTPException(status_code=404, detail=f"Unknown MCP tool: {tool_name}")

    except HTTPException:
        raise
    except Exception as exc:
        return MCPToolExecutionResponse(
            tool_name=tool_name,
            status="error",
            result=None,
            error=str(exc),
        )
