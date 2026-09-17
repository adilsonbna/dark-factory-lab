import hashlib

from agents.ports import StructuredModelAdapter
from agents.schemas import (
    AgentAttribution,
    AgentRole,
    IncidentSignal,
    TriageDecision,
    TriageOutput,
)


class TriageAgent:
    PROMPT_VERSION = "triage-v1"

    def __init__(self, model: StructuredModelAdapter, repository_revision: str):
        self.model = model
        self.repository_revision = repository_revision

    async def run(self, signal: IncidentSignal) -> TriageDecision:
        output = await self.model.generate_structured(
            role=AgentRole.TRIAGE,
            prompt_version=self.PROMPT_VERSION,
            input_data={
                "incident": signal.model_dump(mode="json"),
                "policy": {
                    "allowed_severities": ["low", "medium"],
                    "duplicate_candidates": signal.duplicate_candidates,
                },
            },
            response_model=TriageOutput,
        )
        if not isinstance(output, TriageOutput):
            output = TriageOutput.model_validate(output)
        if output.is_duplicate and output.duplicate_of not in signal.duplicate_candidates:
            raise ValueError("triage decision references an incident outside duplicate_candidates")

        decision_id = self._decision_id(signal.incident_id, output)
        return TriageDecision(
            **output.model_dump(),
            decision_id=decision_id,
            incident_id=signal.incident_id,
            attribution=AgentAttribution(
                role=AgentRole.TRIAGE,
                provider=self.model.provider_name,
                model=self.model.model_name,
                prompt_version=self.PROMPT_VERSION,
                repository_revision=self.repository_revision,
                correlation_id=signal.correlation_id,
            ),
        )

    @staticmethod
    def _decision_id(incident_id: str, output: TriageOutput) -> str:
        payload = f"triage:{incident_id}:{output.model_dump_json()}"
        return f"decision-{hashlib.sha256(payload.encode()).hexdigest()[:20]}"
