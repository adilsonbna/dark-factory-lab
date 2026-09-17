import hashlib

from agents.ports import ObservabilityGateway, StructuredModelAdapter
from agents.schemas import (
    AgentAttribution,
    AgentRole,
    EvidenceKind,
    IncidentSignal,
    InvestigationDecision,
    InvestigationOutput,
    TriageDecision,
)


class InvestigationAgent:
    PROMPT_VERSION = "investigation-v1"

    def __init__(
        self,
        model: StructuredModelAdapter,
        observability: ObservabilityGateway,
        repository_revision: str,
    ):
        self.model = model
        self.observability = observability
        self.repository_revision = repository_revision

    async def run(
        self,
        signal: IncidentSignal,
        triage: TriageDecision,
    ) -> InvestigationDecision:
        evidence = await self.observability.collect_evidence(
            service=triage.affected_service,
            window_start=triage.window_start,
            window_end=triage.window_end,
            correlation_id=signal.correlation_id,
        )
        if not evidence.records:
            raise ValueError("investigation requires observability evidence")

        output = await self.model.generate_structured(
            role=AgentRole.INVESTIGATION,
            prompt_version=self.PROMPT_VERSION,
            input_data={
                "incident": signal.model_dump(mode="json"),
                "triage": triage.model_dump(mode="json"),
                "evidence": [record.model_dump(mode="json") for record in evidence.records],
                "policy": {
                    "cite_only_supplied_evidence": True,
                    "required_signal_kinds": [kind.value for kind in EvidenceKind],
                },
            },
            response_model=InvestigationOutput,
        )
        if not isinstance(output, InvestigationOutput):
            output = InvestigationOutput.model_validate(output)

        available = {record.evidence_id: record for record in evidence.records}
        cited = set(output.evidence_ids)
        unknown = cited - set(available)
        if unknown:
            raise ValueError(f"investigation cited unknown evidence IDs: {sorted(unknown)}")
        cited_kinds = {available[evidence_id].kind for evidence_id in cited}
        missing_kinds = set(EvidenceKind) - cited_kinds
        if missing_kinds:
            names = sorted(kind.value for kind in missing_kinds)
            raise ValueError(f"investigation must correlate logs, metrics, and traces; missing: {names}")
        allowed_root = f"services/{triage.affected_service}"
        invalid_scope = [
            path
            for path in output.allowed_remediation_scope
            if path != allowed_root and not path.startswith(f"{allowed_root}/")
        ]
        if invalid_scope:
            raise ValueError(
                f"investigation proposed remediation outside {allowed_root}: {invalid_scope}"
            )

        decision_id = self._decision_id(signal.incident_id, output)
        return InvestigationDecision(
            **output.model_dump(),
            decision_id=decision_id,
            incident_id=signal.incident_id,
            attribution=AgentAttribution(
                role=AgentRole.INVESTIGATION,
                provider=self.model.provider_name,
                model=self.model.model_name,
                prompt_version=self.PROMPT_VERSION,
                repository_revision=self.repository_revision,
                correlation_id=signal.correlation_id,
            ),
            tool_calls=evidence.tool_calls,
        )

    @staticmethod
    def _decision_id(incident_id: str, output: InvestigationOutput) -> str:
        payload = f"investigation:{incident_id}:{output.model_dump_json()}"
        return f"decision-{hashlib.sha256(payload.encode()).hexdigest()[:20]}"
