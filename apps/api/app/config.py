import os
from pydantic import BaseModel


class Settings(BaseModel):
    CLICKHOUSE_HOST: str = os.getenv("CLICKHOUSE_HOST", "clickhouse")
    CLICKHOUSE_PORT: int = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    CLICKHOUSE_USER: str = os.getenv("CLICKHOUSE_USER", "default")
    CLICKHOUSE_PASSWORD: str = os.getenv("CLICKHOUSE_PASSWORD", "clickhouse")
    CLICKHOUSE_DB: str = os.getenv("CLICKHOUSE_DB", "telemetry")
    OPERATOR_TOKEN: str | None = os.getenv("OPERATOR_TOKEN")

    @property
    def clickhouse_url(self) -> str:
        return f"http://{self.CLICKHOUSE_HOST}:{self.CLICKHOUSE_PORT}"


settings = Settings()
