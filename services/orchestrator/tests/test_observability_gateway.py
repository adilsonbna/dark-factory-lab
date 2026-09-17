import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from agents import EvidenceKind, MCPObservabilityGateway


NOW = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_gateway_collects_bounded_log_metric_and_trace_evidence():
    calls = []

    async def handler(request):
        body = json.loads(request.content)
        query = body["arguments"]["query"]
        calls.append(query)
        if "otel_logs" in query:
            row = {"Body": "ValueError", "ServiceName": "inventory"}
        elif "otel_metrics_sum" in query:
            row = {"MetricName": "error_rate", "Value": 1, "ServiceName": "inventory"}
        else:
            row = {"TraceId": "trace-1", "SpanName": "lookup", "ServiceName": "inventory"}
        return httpx.Response(
            200,
            json={"status": "success", "result": {"data": [row]}},
        )

    gateway = MCPObservabilityGateway(
        api_url="http://api.test",
        limit_per_kind=25,
        transport=httpx.MockTransport(handler),
    )

    bundle = await gateway.collect_evidence(
        service="inventory",
        window_start=NOW - timedelta(minutes=5),
        window_end=NOW,
        correlation_id="run-001",
    )

    assert {record.kind for record in bundle.records} == set(EvidenceKind)
    assert len(bundle.tool_calls) == 3
    assert all(call.status == "success" for call in bundle.tool_calls)
    assert all("LIMIT 25" in query for query in calls)
    assert all("ServiceName = 'inventory'" in query for query in calls)


@pytest.mark.asyncio
async def test_gateway_rejects_unsafe_service_before_network_access():
    gateway = MCPObservabilityGateway(
        transport=httpx.MockTransport(lambda _request: pytest.fail("network should not run"))
    )

    with pytest.raises(ValueError, match="unsupported characters"):
        await gateway.collect_evidence(
            service="inventory' OR 1=1",
            window_start=NOW - timedelta(minutes=5),
            window_end=NOW,
            correlation_id="run-001",
        )
