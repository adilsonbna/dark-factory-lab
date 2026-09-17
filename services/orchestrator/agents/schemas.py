from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AgentRole(str, Enum):
    TRIAGE = "triage"
    INVESTIGATION = "investigation"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"


class EvidenceKind(str, Enum):
    LOG = "log"
    METRIC = "metric"
    TRACE = "trace"


class IncidentSignal(StrictModel):
    incident_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")
    correlation_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(min_length=1, max_length=4000)
    detected_at: datetime
    source: str = Field(min_length=1, max_length=128)
    candidate_service: Optional[str] = Field(
        default=None,
        max_length=128,
        pattern=r"^[A-Za-z0-9_.:-]+$",
    )
    attributes: Dict[str, Any] = Field(default_factory=dict)
    duplicate_candidates: List[str] = Field(default_factory=list, max_length=20)


class ToolCallRecord(StrictModel):
    tool_name: str = Field(min_length=1, max_length=128)
    arguments: Dict[str, Any]
    status: str = Field(pattern=r"^(success|error|denied)$")
    evidence_ids: List[str] = Field(default_factory=list)
    error: Optional[str] = Field(default=None, max_length=1000)


class EvidenceRecord(StrictModel):
    evidence_id: str = Field(min_length=1, max_length=128)
    kind: EvidenceKind
    service: str = Field(min_length=1, max_length=128)
    observed_at: Optional[datetime] = None
    summary: str = Field(min_length=1, max_length=2000)
    payload: Dict[str, Any]


class EvidenceBundle(StrictModel):
    records: List[EvidenceRecord]
    tool_calls: List[ToolCallRecord]


class TriageOutput(StrictModel):
    classification: str = Field(min_length=1, max_length=128)
    severity: Severity
    affected_service: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9_.:-]+$",
    )
    window_start: datetime
    window_end: datetime
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    rationale: str = Field(min_length=1, max_length=4000)

    @model_validator(mode="after")
    def validate_window_and_duplicate(self):
        if self.window_start >= self.window_end:
            raise ValueError("telemetry window_start must be earlier than window_end")
        if self.is_duplicate != bool(self.duplicate_of):
            raise ValueError("duplicate_of must be set if and only if is_duplicate is true")
        return self


class InvestigationOutput(StrictModel):
    root_cause_hypothesis: str = Field(min_length=1, max_length=6000)
    confidence: float = Field(ge=0.0, le=1.0)
    risk: Severity
    evidence_ids: List[str] = Field(min_length=1)
    allowed_remediation_scope: List[str] = Field(min_length=1, max_length=20)
    rationale: str = Field(min_length=1, max_length=6000)


class AgentAttribution(StrictModel):
    role: AgentRole
    provider: str = Field(min_length=1, max_length=128)
    model: str = Field(min_length=1, max_length=128)
    prompt_version: str = Field(min_length=1, max_length=128)
    repository_revision: str = Field(min_length=1, max_length=128)
    correlation_id: str = Field(min_length=1, max_length=128)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TriageDecision(TriageOutput):
    decision_id: str
    incident_id: str
    attribution: AgentAttribution


class InvestigationDecision(InvestigationOutput):
    decision_id: str
    incident_id: str
    attribution: AgentAttribution
    tool_calls: List[ToolCallRecord]
