import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Settings:
    api_url: str = os.getenv("API_URL", "http://api:8000")
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    repository_revision: str = os.getenv("REPOSITORY_REVISION", "unknown")


settings = Settings()
