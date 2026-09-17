from datetime import datetime, timedelta, timezone

import pytest

from agents import (
    AgentRole,
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    IncidentAgentPipeline,
    IncidentSignal,
    InvestigationAgent,
    InvestigationOutput,
    Severity,
    ToolCallRecord,
    TriageAgent,
    TriageOutput,
)
from state_machine import IncidentState, IncidentStateMachine


NOW = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)


class FakeModelAdapter:
    provider_name = "fake-provider"
    model_name = "fake-model"

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def generate_structured(
        self,
        *,
        role,
        prompt_version,
        input_data,
        response_model,
    ):
        self.calls.append((role, prompt_version, input_data, response_model))
        return self.responses[role]


class FakeObservabilityGateway:
    def __init__(self, records):
        self.records = records
        self.calls = []

    async def collect_evidence(self, **kwargs):
        self.calls.append(kwargs)
        return EvidenceBundle(
            records=self.records,
            tool_calls=[
                ToolCallRecord(
                    tool_name="clickstack_sql",
                    arguments={"bounded": True},
                    status="success",
                    evidence_ids=[record.evidence_id for record in self.records],
                )
            ],
        )


def signal(**overrides):
    values = {
        "incident_id": "inc-001",
        "correlation_id": "run-001",
        "title": "Inventory errors",
        "summary": "Checkout requests fail while calling inventory",
        "detected_at": NOW,
        "source": "detector",
        "candidate_service": "inventory",
    }
    values.update(overrides)
    return IncidentSignal(**values)


def triage_output(**overrides):
    values = {
        "classification": "application_exception",
        "severity": Severity.MEDIUM,
        "affected_service": "inventory",
        "window_start": NOW - timedelta(minutes=5),
        "window_end": NOW + timedelta(minutes=1),
        "rationale": "Errors are isolated to the inventory dependency.",
    }
    values.update(overrides)
    return TriageOutput(**values)


def evidence_records():
    return [
        EvidenceRecord(
            evidence_id="ev-log",
            kind=EvidenceKind.LOG,
            service="inventory",
            summary="ValueError in inventory handler",
            payload={"Body": "ValueError in inventory handler"},
        ),
        EvidenceRecord(
            evidence_id="ev-metric",
            kind=EvidenceKind.METRIC,
            service="inventory",
            summary="error_rate=1",
            payload={"MetricName": "error_rate", "Value": 1},
        ),
        EvidenceRecord(
            evidence_id="ev-trace",
            kind=EvidenceKind.TRACE,
            service="inventory",
            summary="trace=t-1 span=inventory.lookup",
            payload={"TraceId": "t-1", "SpanName": "inventory.lookup"},
        ),
    ]


def investigation_output(**overrides):
    values = {
        "root_cause_hypothesis": "Inventory raises ValueError during lookup.",
        "confidence": 0.9,
        "risk": Severity.MEDIUM,
        "evidence_ids": ["ev-log", "ev-metric", "ev-trace"],
        "allowed_remediation_scope": ["services/inventory"],
        "rationale": "The exception, error metric, and failing span align in time.",
    }
    values.update(overrides)
    return InvestigationOutput(**values)


@pytest.mark.asyncio
async def test_pipeline_advances_through_fix_proposed_with_attributed_evidence():
    model = FakeModelAdapter(
        {
            AgentRole.TRIAGE: triage_output(),
            AgentRole.INVESTIGATION: investigation_output(),
        }
    )
    gateway = FakeObservabilityGateway(evidence_records())
    pipeline = IncidentAgentPipeline(
        triage_agent=TriageAgent(model, repository_revision="abc123"),
        investigation_agent=InvestigationAgent(
            model,
            gateway,
            repository_revision="abc123",
        ),
        kill_switch_check=_kill_switch_off,
    )
    machine = IncidentStateMachine("inc-001")

    result = await pipeline.run(signal(), machine)

    assert result.final_state == IncidentState.FIX_PROPOSED
    assert [record.to_state for record in machine.history] == [
        IncidentState.TRIAGED,
        IncidentState.INVESTIGATING,
        IncidentState.FIX_PROPOSED,
    ]
    assert result.triage is not None
    assert result.triage.attribution.role == AgentRole.TRIAGE
    assert result.investigation is not None
    assert result.investigation.attribution.role == AgentRole.INVESTIGATION
    assert result.investigation.evidence_ids == ["ev-log", "ev-metric", "ev-trace"]
    assert len(result.investigation.tool_calls) == 1


@pytest.mark.asyncio
async def test_investigation_rejects_evidence_not_returned_by_tools():
    model = FakeModelAdapter(
        {AgentRole.INVESTIGATION: investigation_output(evidence_ids=["ev-invented"])}
    )
    agent = InvestigationAgent(
        model,
        FakeObservabilityGateway(evidence_records()),
        repository_revision="abc123",
    )
    triage_model = FakeModelAdapter({AgentRole.TRIAGE: triage_output()})
    triage = await TriageAgent(triage_model, "abc123").run(signal())

    with pytest.raises(ValueError, match="unknown evidence IDs"):
        await agent.run(signal(), triage)


@pytest.mark.asyncio
async def test_investigation_requires_log_metric_and_trace_correlation():
    records = evidence_records()[:2]
    model = FakeModelAdapter(
        {
            AgentRole.TRIAGE: triage_output(),
            AgentRole.INVESTIGATION: investigation_output(
                evidence_ids=["ev-log", "ev-metric"]
            ),
        }
    )
    triage = await TriageAgent(model, "abc123").run(signal())
    agent = InvestigationAgent(
        model,
        FakeObservabilityGateway(records),
        repository_revision="abc123",
    )

    with pytest.raises(ValueError, match=r"missing: \['trace'\]"):
        await agent.run(signal(), triage)


@pytest.mark.asyncio
async def test_triage_rejects_duplicate_outside_candidate_set():
    model = FakeModelAdapter(
        {
            AgentRole.TRIAGE: triage_output(
                is_duplicate=True,
                duplicate_of="inc-not-authorized",
            )
        }
    )

    with pytest.raises(ValueError, match="outside duplicate_candidates"):
        await TriageAgent(model, "abc123").run(
            signal(duplicate_candidates=["inc-existing"])
        )


@pytest.mark.asyncio
async def test_investigation_rejects_remediation_scope_outside_service():
    model = FakeModelAdapter(
        {
            AgentRole.TRIAGE: triage_output(),
            AgentRole.INVESTIGATION: investigation_output(
                allowed_remediation_scope=["infra/compose"]
            ),
        }
    )
    triage = await TriageAgent(model, "abc123").run(signal())
    agent = InvestigationAgent(
        model,
        FakeObservabilityGateway(evidence_records()),
        repository_revision="abc123",
    )

    with pytest.raises(ValueError, match="outside services/inventory"):
        await agent.run(signal(), triage)


@pytest.mark.asyncio
async def test_pipeline_honors_kill_switch_before_first_transition():
    model = FakeModelAdapter({AgentRole.TRIAGE: triage_output()})
    gateway = FakeObservabilityGateway(evidence_records())
    pipeline = IncidentAgentPipeline(
        triage_agent=TriageAgent(model, "abc123"),
        investigation_agent=InvestigationAgent(model, gateway, "abc123"),
        kill_switch_check=_kill_switch_on,
    )
    machine = IncidentStateMachine("inc-001")

    result = await pipeline.run(signal(), machine)

    assert result.final_state == IncidentState.ESCALATED
    assert result.triage is None
    assert result.investigation is None
    assert len(model.calls) == 0
    assert gateway.calls == []


async def _kill_switch_off():
    return False


async def _kill_switch_on():
    return True
