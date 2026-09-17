from typing import Awaitable, Callable, Optional

from pydantic import BaseModel, ConfigDict

from agents.investigation import InvestigationAgent
from agents.schemas import IncidentSignal, InvestigationDecision, TriageDecision
from agents.triage import TriageAgent
from state_machine import IncidentState, IncidentStateMachine


KillSwitchCheck = Callable[[], Awaitable[bool]]


class PipelineResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str
    final_state: IncidentState
    triage: Optional[TriageDecision] = None
    investigation: Optional[InvestigationDecision] = None


class IncidentAgentPipeline:
    def __init__(
        self,
        triage_agent: TriageAgent,
        investigation_agent: InvestigationAgent,
        kill_switch_check: KillSwitchCheck,
    ):
        self.triage_agent = triage_agent
        self.investigation_agent = investigation_agent
        self.kill_switch_check = kill_switch_check

    async def run(
        self,
        signal: IncidentSignal,
        state_machine: IncidentStateMachine,
    ) -> PipelineResult:
        if state_machine.incident_id != signal.incident_id:
            raise ValueError("state machine and signal incident IDs must match")
        if state_machine.state != IncidentState.DETECTED:
            raise ValueError("agent pipeline requires an incident in Detected state")

        if await self.kill_switch_check():
            state_machine.transition_to(
                IncidentState.TRIAGED,
                actor="Orchestrator",
                evidence_id="KILL_SWITCH_ACTIVE",
                policy_decision="Agent execution denied by operator kill switch",
                kill_switch_active=True,
            )
            return PipelineResult(
                incident_id=signal.incident_id,
                final_state=state_machine.state,
            )

        triage = await self.triage_agent.run(signal)
        triage_record = state_machine.transition_to(
            IncidentState.TRIAGED,
            actor="TriageAgent",
            evidence_id=triage.decision_id,
            policy_decision="Validated structured triage decision",
            details=triage.model_dump(mode="json"),
            kill_switch_active=await self.kill_switch_check(),
        )
        if triage_record.to_state == IncidentState.ESCALATED or triage.is_duplicate:
            return PipelineResult(
                incident_id=signal.incident_id,
                final_state=state_machine.state,
                triage=triage,
            )

        investigating_record = state_machine.transition_to(
            IncidentState.INVESTIGATING,
            actor="Orchestrator",
            evidence_id=triage.decision_id,
            policy_decision="Triage accepted; investigation authorized",
            kill_switch_active=await self.kill_switch_check(),
        )
        if investigating_record.to_state == IncidentState.ESCALATED:
            return PipelineResult(
                incident_id=signal.incident_id,
                final_state=state_machine.state,
                triage=triage,
            )

        investigation = await self.investigation_agent.run(signal, triage)
        state_machine.transition_to(
            IncidentState.FIX_PROPOSED,
            actor="InvestigationAgent",
            evidence_id=investigation.decision_id,
            policy_decision="Evidence-grounded investigation accepted",
            details=investigation.model_dump(mode="json"),
            kill_switch_active=await self.kill_switch_check(),
        )
        return PipelineResult(
            incident_id=signal.incident_id,
            final_state=state_machine.state,
            triage=triage,
            investigation=investigation,
        )
