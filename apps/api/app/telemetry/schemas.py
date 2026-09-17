from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SQLQueryRequest(BaseModel):
    query: str = Field(..., description="SQL query to execute against ClickHouse telemetry database (must be read-only)")


class SQLQueryResponse(BaseModel):
    query: str
    rows: int
    data: List[Dict[str, Any]]
    meta: Optional[List[Dict[str, Any]]] = None
    elapsed_seconds: Optional[float] = None


class TelemetryHealthResponse(BaseModel):
    status: str
    clickhouse_url: str
    tables: List[str]


class MetricQueryRequest(BaseModel):
    metric_name: Optional[str] = None
    service_name: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=1000)


class TraceQueryRequest(BaseModel):
    trace_id: Optional[str] = None
    service_name: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=1000)


class LogQueryRequest(BaseModel):
    service_name: Optional[str] = None
    query_text: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=1000)
