import pytest
from fastapi import HTTPException
from app.telemetry.client import validate_read_only_query


def test_allowed_read_only_queries():
    assert validate_read_only_query("SELECT * FROM telemetry.otel_logs") == "SELECT * FROM telemetry.otel_logs"
    assert validate_read_only_query("SHOW TABLES") == "SHOW TABLES"
    assert validate_read_only_query("DESCRIBE TABLE telemetry.otel_traces") == "DESCRIBE TABLE telemetry.otel_traces"
    assert validate_read_only_query("EXPLAIN SELECT 1") == "EXPLAIN SELECT 1"
    assert validate_read_only_query("WITH cte AS (SELECT 1) SELECT * FROM cte") == "WITH cte AS (SELECT 1) SELECT * FROM cte"


def test_prohibited_mutation_queries():
    prohibited_queries = [
        "DROP TABLE telemetry.otel_logs",
        "DELETE FROM telemetry.otel_traces WHERE 1=1",
        "INSERT INTO telemetry.otel_logs VALUES ('fake')",
        "ALTER TABLE telemetry.otel_traces DROP COLUMN SpanId",
        "TRUNCATE TABLE telemetry.otel_metrics_sum",
        "SELECT * FROM telemetry.otel_logs; DROP TABLE telemetry.otel_logs",
    ]

    for q in prohibited_queries:
        with pytest.raises(HTTPException) as exc_info:
            validate_read_only_query(q)
        assert exc_info.value.status_code == 400
        assert "Security violation" in exc_info.value.detail
