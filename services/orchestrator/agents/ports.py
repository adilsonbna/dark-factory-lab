import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, Protocol, Type, TypeVar

import httpx
from pydantic import BaseModel

from agents.schemas import (
    AgentRole,
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    ToolCallRecord,
)


ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class StructuredModelAdapter(Protocol):
    provider_name: str
    model_name: str

    async def generate_structured(
        self,
        *,
        role: AgentRole,
        prompt_version: str,
        input_data: Dict[str, Any],
        response_model: Type[ResponseModel],
    ) -> ResponseModel: ...


class ObservabilityGateway(Protocol):
    async def collect_evidence(
        self,
        *,
        service: str,
        window_start: datetime,
        window_end: datetime,
        correlation_id: str,
    ) -> EvidenceBundle: ...


class MCPObservabilityGateway:
    """Read-only observability access through the backend's MCP boundary."""

    _TABLE_QUERIES = {
        EvidenceKind.LOG: (
            "SELECT Timestamp, ServiceName, Body, SeverityText "
            "FROM telemetry.otel_logs"
        ),
        EvidenceKind.METRIC: (
            "SELECT TimeUnix, ServiceName, MetricName, Value "
            "FROM telemetry.otel_metrics_sum"
        ),
        EvidenceKind.TRACE: (
            "SELECT Timestamp, ServiceName, SpanName, TraceId, SpanId, Duration "
            "FROM telemetry.otel_traces"
        ),
    }
    _TIME_COLUMNS = {
        EvidenceKind.LOG: "Timestamp",
        EvidenceKind.METRIC: "TimeUnix",
        EvidenceKind.TRACE: "Timestamp",
    }

    def __init__(
        self,
        api_url: str = "http://api:8000",
        limit_per_kind: int = 100,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        if not 1 <= limit_per_kind <= 1000:
            raise ValueError("limit_per_kind must be between 1 and 1000")
        self.api_url = api_url.rstrip("/")
        self.limit_per_kind = limit_per_kind
        self._transport = transport

    async def collect_evidence(
        self,
        *,
        service: str,
        window_start: datetime,
        window_end: datetime,
        correlation_id: str,
    ) -> EvidenceBundle:
        if not re.fullmatch(r"[A-Za-z0-9_.:-]+", service):
            raise ValueError("service contains unsupported characters")
        if window_start >= window_end:
            raise ValueError("window_start must be earlier than window_end")
        records = []
        tool_calls = []
        async with httpx.AsyncClient(timeout=15.0, transport=self._transport) as client:
            for kind, select_clause in self._TABLE_QUERIES.items():
                time_column = self._TIME_COLUMNS[kind]
                query = (
                    f"{select_clause} WHERE ServiceName = '{service}' "
                    f"AND {time_column} >= parseDateTimeBestEffort('{window_start.isoformat()}') "
                    f"AND {time_column} <= parseDateTimeBestEffort('{window_end.isoformat()}') "
                    f"ORDER BY {time_column} DESC LIMIT {self.limit_per_kind}"
                )
                arguments = {"query": query}
                response = await client.post(
                    f"{self.api_url}/api/v1/mcp/execute",
                    json={"tool_name": "clickstack_sql", "arguments": arguments},
                )
                response.raise_for_status()
                body = response.json()
                if body.get("status") != "success":
                    tool_calls.append(
                        ToolCallRecord(
                            tool_name="clickstack_sql",
                            arguments=arguments,
                            status="error",
                            error=body.get("error", "unknown MCP error"),
                        )
                    )
                    continue

                rows = (body.get("result") or {}).get("data", [])
                evidence_ids = []
                for row in rows:
                    evidence_id = self._evidence_id(kind, correlation_id, row)
                    evidence_ids.append(evidence_id)
                    records.append(
                        EvidenceRecord(
                            evidence_id=evidence_id,
                            kind=kind,
                            service=service,
                            summary=self._summary(kind, row),
                            payload=row,
                        )
                    )
                tool_calls.append(
                    ToolCallRecord(
                        tool_name="clickstack_sql",
                        arguments=arguments,
                        status="success",
                        evidence_ids=evidence_ids,
                    )
                )
        return EvidenceBundle(records=records, tool_calls=tool_calls)

    @staticmethod
    def _evidence_id(kind: EvidenceKind, correlation_id: str, row: Dict[str, Any]) -> str:
        canonical = json.dumps(row, sort_keys=True, default=str, separators=(",", ":"))
        digest = hashlib.sha256(f"{kind.value}:{correlation_id}:{canonical}".encode()).hexdigest()
        return f"ev-{digest[:20]}"

    @staticmethod
    def _summary(kind: EvidenceKind, row: Dict[str, Any]) -> str:
        if kind == EvidenceKind.LOG:
            return str(row.get("Body") or row.get("body") or "log record")[:2000]
        if kind == EvidenceKind.METRIC:
            return f"{row.get('MetricName', 'metric')}={row.get('Value', 'unknown')}"[:2000]
        return f"trace={row.get('TraceId', 'unknown')} span={row.get('SpanName', 'unknown')}"[:2000]
