import asyncio
import logging
from typing import Dict, Optional
import httpx

from agents import (
    IncidentAgentPipeline,
    IncidentSignal,
    InvestigationAgent,
    MCPObservabilityGateway,
    ObservabilityGateway,
    PipelineResult,
    StructuredModelAdapter,
    TriageAgent,
)
from state_machine import IncidentState, IncidentStateMachine

logger = logging.getLogger("orchestrator.engine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class OrchestratorEngine:
    def __init__(self, api_url: str = "http://api:8000"):
        self.api_url = api_url
        self.machines: Dict[str, IncidentStateMachine] = {}
        self.agent_pipeline: Optional[IncidentAgentPipeline] = None

    def configure_agents(
        self,
        *,
        model: StructuredModelAdapter,
        repository_revision: str,
        observability: Optional[ObservabilityGateway] = None,
    ) -> None:
        evidence_gateway = observability or MCPObservabilityGateway(api_url=self.api_url)
        self.agent_pipeline = IncidentAgentPipeline(
            triage_agent=TriageAgent(model, repository_revision),
            investigation_agent=InvestigationAgent(
                model,
                evidence_gateway,
                repository_revision,
            ),
            kill_switch_check=self.get_kill_switch_active,
        )

    async def get_kill_switch_active(self) -> bool:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                res = await client.get(f"{self.api_url}/api/v1/dashboard/devops")
                if res.status_code == 200:
                    return res.json().get("kill_switch_active", False)
            except Exception as e:
                logger.error(f"Failed to check kill switch status from API: {e}")
        return False

    def get_or_create_machine(self, incident_id: str) -> IncidentStateMachine:
        if incident_id not in self.machines:
            self.machines[incident_id] = IncidentStateMachine(incident_id=incident_id)
        return self.machines[incident_id]

    async def process_incident_step(self, incident_id: str, target_state: IncidentState, actor: str, evidence_id: str, decision: str):
        kill_switch = await self.get_kill_switch_active()
        sm = self.get_or_create_machine(incident_id)

        try:
            record = sm.transition_to(
                next_state=target_state,
                actor=actor,
                evidence_id=evidence_id,
                policy_decision=decision,
                kill_switch_active=kill_switch,
            )
            logger.info(f"Processed step for {incident_id}: {record.to_state.value}")
            return record
        except Exception as exc:
            logger.error(f"Error processing step for {incident_id}: {exc}")
            raise

    async def process_signal(self, signal: IncidentSignal) -> PipelineResult:
        if self.agent_pipeline is None:
            raise RuntimeError("Milestone 7 agents are not configured")
        machine = self.get_or_create_machine(signal.incident_id)
        return await self.agent_pipeline.run(signal, machine)

    async def run_loop(self):
        logger.info("Deterministic Orchestrator Engine initialized.")
        while True:
            try:
                kill_switch = await self.get_kill_switch_active()
                if kill_switch:
                    logger.warning("Kill switch is ACTIVE. Orchestrator sleeping...")
                else:
                    logger.debug("Orchestrator heartbeat OK.")
            except Exception as exc:
                logger.error(f"Orchestrator loop error: {exc}")
            await asyncio.sleep(5)
