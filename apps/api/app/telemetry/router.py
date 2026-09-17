from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.telemetry.client import clickhouse_client
from app.telemetry.schemas import (
    LogQueryRequest,
    MetricQueryRequest,
    SQLQueryRequest,
    SQLQueryResponse,
    TelemetryHealthResponse,
    TraceQueryRequest,
)

router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])


@router.get("/health", response_model=TelemetryHealthResponse)
async def telemetry_health():
    try:
        tables = await clickhouse_client.get_tables()
        return TelemetryHealthResponse(
            status="ok",
            clickhouse_url=clickhouse_client.base_url,
            tables=tables,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"ClickHouse telemetry unhealthy: {exc}")


@router.post("/sql", response_model=SQLQueryResponse)
async def execute_sql(body: SQLQueryRequest):
    result = await clickhouse_client.execute_query(body.query)
    data = result.get("data", [])
    meta = result.get("meta", [])
    rows = result.get("rows", len(data))
    elapsed = result.get("statistics", {}).get("elapsed")

    return SQLQueryResponse(
        query=body.query,
        rows=rows,
        data=data,
        meta=meta,
        elapsed_seconds=elapsed,
    )


@router.get("/metrics")
async def query_metrics(
    metric_name: Optional[str] = Query(None),
    service_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
):
    where_clauses = []
    if metric_name:
        where_clauses.append(f"MetricName = '{metric_name}'")
    if service_name:
        where_clauses.append(f"ServiceName = '{service_name}'")

    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    sql = f"SELECT MetricName, Value, ServiceName, TimeUnix FROM telemetry.otel_metrics_sum {where_str} ORDER BY TimeUnix DESC LIMIT {limit}"

    return await clickhouse_client.execute_query(sql)


@router.get("/traces")
async def query_traces(
    trace_id: Optional[str] = Query(None),
    service_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
):
    where_clauses = []
    if trace_id:
        where_clauses.append(f"TraceId = '{trace_id}'")
    if service_name:
        where_clauses.append(f"ServiceName = '{service_name}'")

    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    sql = f"SELECT ServiceName, SpanName, TraceId, SpanId, ParentSpanId, Duration, Timestamp FROM telemetry.otel_traces {where_str} ORDER BY Timestamp DESC LIMIT {limit}"

    return await clickhouse_client.execute_query(sql)


@router.get("/logs")
async def query_logs(
    service_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
):
    where_clauses = []
    if service_name:
        where_clauses.append(f"ServiceName = '{service_name}'")

    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    sql = f"SELECT Timestamp, ServiceName, Body, SeverityText FROM telemetry.otel_logs {where_str} ORDER BY Timestamp DESC LIMIT {limit}"

    return await clickhouse_client.execute_query(sql)
