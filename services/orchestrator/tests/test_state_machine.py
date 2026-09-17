import pytest
from state_machine import IncidentState, IncidentStateMachine


def test_happy_path_transitions():
    sm = IncidentStateMachine(incident_id="inc-test-01")
    assert sm.state == IncidentState.DETECTED

    sm.transition_to(IncidentState.TRIAGED, actor="TriageAgent", evidence_id="EVD-01", policy_decision="POL-01")
    assert sm.state == IncidentState.TRIAGED

    sm.transition_to(IncidentState.INVESTIGATING, actor="InvestigationAgent", evidence_id="EVD-02", policy_decision="POL-02")
    assert sm.state == IncidentState.INVESTIGATING

    sm.transition_to(IncidentState.FIX_PROPOSED, actor="RemediationAgent", evidence_id="EVD-03", policy_decision="POL-03")
    assert sm.state == IncidentState.FIX_PROPOSED

    sm.transition_to(IncidentState.VALIDATING, actor="ValidationAgent", evidence_id="EVD-04", policy_decision="POL-04")
    assert sm.state == IncidentState.VALIDATING

    sm.transition_to(IncidentState.APPROVED, actor="ValidationAgent", evidence_id="EVD-05", policy_decision="POL-05")
    assert sm.state == IncidentState.APPROVED

    sm.transition_to(IncidentState.DEPLOYING, actor="ReleaseAgent", evidence_id="EVD-06", policy_decision="POL-06")
    assert sm.state == IncidentState.DEPLOYING

    sm.transition_to(IncidentState.OBSERVING, actor="ReleaseAgent", evidence_id="EVD-07", policy_decision="POL-07")
    assert sm.state == IncidentState.OBSERVING

    sm.transition_to(IncidentState.RESOLVED, actor="Orchestrator", evidence_id="EVD-08", policy_decision="POL-08")
    assert sm.state == IncidentState.RESOLVED

    assert len(sm.history) == 8
    assert len(sm.audit_log) == 8


def test_invalid_transition_rejection():
    sm = IncidentStateMachine(incident_id="inc-test-02")
    # Illegal jump: Detected directly to Resolved
    with pytest.raises(ValueError) as exc_info:
        sm.transition_to(IncidentState.RESOLVED, actor="BadActor", evidence_id="EVD-99", policy_decision="POL-99")
    assert "Invalid state transition" in str(exc_info.value)
    assert sm.state == IncidentState.DETECTED


def test_circuit_breaker_escalation():
    sm = IncidentStateMachine(incident_id="inc-test-retry")
    sm.transition_to(IncidentState.TRIAGED, actor="TriageAgent", evidence_id="EVD-01", policy_decision="POL-01")
    sm.transition_to(IncidentState.INVESTIGATING, actor="InvestigationAgent", evidence_id="EVD-02", policy_decision="POL-02")
    sm.transition_to(IncidentState.FIX_PROPOSED, actor="RemediationAgent", evidence_id="EVD-03", policy_decision="POL-03")

    # Attempt 1: Validating -> Fix proposed (retry 1)
    sm.transition_to(IncidentState.VALIDATING, actor="ValidationAgent", evidence_id="EVD-04", policy_decision="POL-04")
    sm.transition_to(IncidentState.FIX_PROPOSED, actor="RemediationAgent", evidence_id="EVD-05", policy_decision="Retry 1")
    assert sm.retry_count == 1

    # Attempt 2: Validating -> Fix proposed (retry 2)
    sm.transition_to(IncidentState.VALIDATING, actor="ValidationAgent", evidence_id="EVD-06", policy_decision="POL-06")
    sm.transition_to(IncidentState.FIX_PROPOSED, actor="RemediationAgent", evidence_id="EVD-07", policy_decision="Retry 2")
    assert sm.retry_count == 2

    # Attempt 3: Validating -> Fix proposed (retry 3)
    sm.transition_to(IncidentState.VALIDATING, actor="ValidationAgent", evidence_id="EVD-08", policy_decision="POL-08")
    sm.transition_to(IncidentState.FIX_PROPOSED, actor="RemediationAgent", evidence_id="EVD-09", policy_decision="Retry 3")
    assert sm.retry_count == 3

    # Attempt 4: Exceeds MAX_RETRY_ATTEMPTS (3) -> Circuit breaker forces ESCALATED
    sm.transition_to(IncidentState.VALIDATING, actor="ValidationAgent", evidence_id="EVD-10", policy_decision="POL-10")
    record = sm.transition_to(IncidentState.FIX_PROPOSED, actor="RemediationAgent", evidence_id="EVD-11", policy_decision="Retry 4")

    assert sm.state == IncidentState.ESCALATED
    assert record.actor == "CircuitBreaker"
    assert "Circuit breaker triggered" in record.policy_decision


def test_kill_switch_escalation():
    sm = IncidentStateMachine(incident_id="inc-test-kill")
    sm.transition_to(IncidentState.TRIAGED, actor="TriageAgent", evidence_id="EVD-01", policy_decision="POL-01")

    # Attempt transition while kill switch is active
    record = sm.transition_to(
        IncidentState.INVESTIGATING,
        actor="InvestigationAgent",
        evidence_id="EVD-02",
        policy_decision="POL-02",
        kill_switch_active=True,
    )

    assert sm.state == IncidentState.ESCALATED
    assert record.actor == "KillSwitch"
    assert "Emergency halt" in record.policy_decision
