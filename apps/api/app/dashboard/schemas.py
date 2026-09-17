from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class IncidentItem(BaseModel):
    id: str
    title: str
    status: str  # Detected, Triaged, Investigating, Fix proposed, Validating, Approved, Deploying, Observing, Resolved, Rolled back, Escalated
    severity: str  # low, medium, high
    affected_service: str
    detected_at: datetime
    hypothesis: Optional[str] = None
    root_cause: Optional[str] = None
    remediation_pr_url: Optional[str] = None
    remediation_diff: Optional[str] = None
    retry_count: int = 0
    agent_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)


class DevOpsViewResponse(BaseModel):
    kill_switch_active: bool
    active_incidents: List[IncidentItem]
    resolved_incidents: List[IncidentItem]
    recent_telemetry_summary: Dict[str, Any]


class ManagementViewResponse(BaseModel):
    overall_health: str  # HEALTHY, DEGRADED, CRITICAL
    open_incidents_count: int
    resolved_incidents_count: int
    mean_detection_seconds: Optional[float] = None
    mean_diagnosis_seconds: Optional[float] = None
    mean_recovery_seconds: Optional[float] = None
    mean_rollback_seconds: Optional[float] = None
    remediation_success_rate_percent: Optional[float] = None
    false_alert_rate_percent: Optional[float] = None
    failed_remediation_rate_percent: Optional[float] = None
    llm_usage_total_tokens: Optional[int] = None
    llm_estimated_cost_usd: Optional[float] = None
    release_qualification_status: str


class KillSwitchRequest(BaseModel):
    active: bool
    reason: Optional[str] = "Operator manual override"


class KillSwitchResponse(BaseModel):
    active: bool
    timestamp: datetime
    message: str
