from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("orchestrator.state_machine")


class IncidentState(str, Enum):
    DETECTED = "Detected"
    TRIAGED = "Triaged"
    INVESTIGATING = "Investigating"
    FIX_PROPOSED = "Fix proposed"
    VALIDATING = "Validating"
    APPROVED = "Approved"
    DEPLOYING = "Deploying"
    OBSERVING = "Observing"
    RESOLVED = "Resolved"
    ROLLED_BACK = "Rolled back"
    ESCALATED = "Escalated"


# Allowed state transitions (intent.md §11)
ALLOWED_TRANSITIONS: Dict[IncidentState, List[IncidentState]] = {
    IncidentState.DETECTED: [IncidentState.TRIAGED, IncidentState.ESCALATED],
    IncidentState.TRIAGED: [IncidentState.INVESTIGATING, IncidentState.ESCALATED],
    IncidentState.INVESTIGATING: [IncidentState.FIX_PROPOSED, IncidentState.ESCALATED],
    IncidentState.FIX_PROPOSED: [IncidentState.VALIDATING, IncidentState.ESCALATED],
    IncidentState.VALIDATING: [IncidentState.APPROVED, IncidentState.FIX_PROPOSED, IncidentState.ESCALATED],
    IncidentState.APPROVED: [IncidentState.DEPLOYING, IncidentState.ESCALATED],
    IncidentState.DEPLOYING: [IncidentState.OBSERVING, IncidentState.ROLLED_BACK, IncidentState.ESCALATED],
    IncidentState.OBSERVING: [IncidentState.RESOLVED, IncidentState.ROLLED_BACK, IncidentState.ESCALATED],
    IncidentState.ROLLED_BACK: [IncidentState.FIX_PROPOSED, IncidentState.ESCALATED],
    IncidentState.RESOLVED: [],  # Terminal state
    IncidentState.ESCALATED: [], # Terminal state
}

MAX_RETRY_ATTEMPTS = 3


class StateTransitionRecord(BaseModel):
    from_state: IncidentState
    to_state: IncidentState
    timestamp: datetime
    actor: str
    evidence_id: str
    policy_decision: str
    details: Optional[Dict[str, Any]] = None


class IncidentStateMachine:
    def __init__(self, incident_id: str, initial_state: IncidentState = IncidentState.DETECTED):
        self.incident_id = incident_id
        self.state = initial_state
        self.retry_count = 0
        self.history: List[StateTransitionRecord] = []
        self.audit_log: List[Dict[str, Any]] = []

    def transition_to(
        self,
        next_state: IncidentState,
        actor: str,
        evidence_id: str,
        policy_decision: str,
        details: Optional[Dict[str, Any]] = None,
        kill_switch_active: bool = False,
    ) -> StateTransitionRecord:
        # Check Kill Switch override per REQ-UI-03 & intent.md §9
        if kill_switch_active:
            logger.warning(f"Kill switch active! Halting forward transition for incident {self.incident_id}.")
            return self._force_escalation(
                actor="KillSwitch",
                evidence_id="KILL_SWITCH_ACTIVE",
                policy_decision="Emergency halt by operator kill switch",
            )

        # Check terminal state
        if self.state in (IncidentState.RESOLVED, IncidentState.ESCALATED):
            raise ValueError(f"Cannot transition from terminal state {self.state.value}")

        # Check allowed transition
        allowed = ALLOWED_TRANSITIONS.get(self.state, [])
        if next_state not in allowed:
            raise ValueError(f"Invalid state transition: {self.state.value} -> {next_state.value}. Allowed: {[s.value for s in allowed]}")

        # Handle retry policy (intent.md §12): If returning to FIX_PROPOSED due to validation/deploy failure
        if next_state == IncidentState.FIX_PROPOSED and self.state in (IncidentState.VALIDATING, IncidentState.ROLLED_BACK):
            self.retry_count += 1
            logger.info(f"Incident {self.incident_id} retry attempt {self.retry_count}/{MAX_RETRY_ATTEMPTS}")
            if self.retry_count > MAX_RETRY_ATTEMPTS:
                logger.error(f"Circuit breaker triggered for incident {self.incident_id}: retry count {self.retry_count} exceeded limit {MAX_RETRY_ATTEMPTS}")
                return self._force_escalation(
                    actor="CircuitBreaker",
                    evidence_id=evidence_id,
                    policy_decision=f"Circuit breaker triggered after {MAX_RETRY_ATTEMPTS} failed attempts",
                )

        record = StateTransitionRecord(
            from_state=self.state,
            to_state=next_state,
            timestamp=datetime.now(timezone.utc),
            actor=actor,
            evidence_id=evidence_id,
            policy_decision=policy_decision,
            details=details,
        )

        old_state = self.state
        self.state = next_state
        self.history.append(record)

        audit_entry = {
            "event": f"TRANSITION_{old_state.value.upper().replace(' ', '_')}_TO_{next_state.value.upper().replace(' ', '_')}",
            "timestamp": record.timestamp.isoformat(),
            "actor": actor,
            "evidence_id": evidence_id,
            "policy_decision": policy_decision,
            "incident_id": self.incident_id,
        }
        self.audit_log.append(audit_entry)

        logger.info(f"Incident {self.incident_id} transitioned: {old_state.value} -> {next_state.value} by {actor}")
        return record

    def _force_escalation(self, actor: str, evidence_id: str, policy_decision: str) -> StateTransitionRecord:
        record = StateTransitionRecord(
            from_state=self.state,
            to_state=IncidentState.ESCALATED,
            timestamp=datetime.now(timezone.utc),
            actor=actor,
            evidence_id=evidence_id,
            policy_decision=policy_decision,
        )
        old_state = self.state
        self.state = IncidentState.ESCALATED
        self.history.append(record)

        self.audit_log.append({
            "event": "INCIDENT_ESCALATED",
            "timestamp": record.timestamp.isoformat(),
            "actor": actor,
            "evidence_id": evidence_id,
            "policy_decision": policy_decision,
            "incident_id": self.incident_id,
        })
        return record
