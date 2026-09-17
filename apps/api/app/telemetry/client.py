import logging
from typing import Any, Dict, List, Optional
import httpx
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger("telemetry.client")

ALLOWED_SQL_PREFIXES = ("SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "WITH")
PROHIBITED_SQL_KEYWORDS = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "RENAME", "GRANT", "REVOKE")


def validate_read_only_query(query: str) -> str:
    cleaned = query.strip().rstrip(";")
    uppercase_query = cleaned.upper()

    if not any(uppercase_query.startswith(prefix) for prefix in ALLOWED_SQL_PREFIXES):
        raise HTTPException(
            status_code=400,
            detail=f"Security violation: Only read-only queries starting with {ALLOWED_SQL_PREFIXES} are allowed."
        )

    for keyword in PROHIBITED_SQL_KEYWORDS:
        if f" {keyword} " in f" {uppercase_query} ":
            raise HTTPException(
                status_code=400,
                detail=f"Security violation: Prohibited SQL keyword '{keyword}' detected in query."
            )

    return cleaned


class ClickHouseClient:
    def __init__(
        self,
        base_url: str = settings.clickhouse_url,
        user: str = settings.CLICKHOUSE_USER,
        password: str = settings.CLICKHOUSE_PASSWORD,
        database: str = settings.CLICKHOUSE_DB,
    ):
        self.base_url = base_url
        self.user = user
        self.password = password
        self.database = database

    async def execute_query(self, query: str) -> Dict[str, Any]:
        sanitized_query = validate_read_only_query(query)
        if "FORMAT" not in sanitized_query.upper():
            sql_to_run = f"{sanitized_query} FORMAT JSON"
        else:
            sql_to_run = sanitized_query

        params = {
            "database": self.database,
            "user": self.user,
            "password": self.password,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    self.base_url,
                    params=params,
                    content=sql_to_run.encode("utf-8"),
                )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"ClickHouse query error: {response.text}",
                    )
                return response.json()
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to connect to ClickHouse at {self.base_url}: {exc}",
                )

    async def get_tables(self) -> List[str]:
        result = await self.execute_query("SHOW TABLES")
        data = result.get("data", [])
        return [row["name"] for row in data if "name" in row]


clickhouse_client = ClickHouseClient()
