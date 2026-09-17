import asyncio
import logging

from agents import GeminiStructuredAdapter
from config import settings
from engine import OrchestratorEngine

logger = logging.getLogger("orchestrator.main")


async def main():
    logger.info("Starting Orchestrator Engine...")
    engine = OrchestratorEngine(api_url=settings.api_url)
    if settings.gemini_api_key:
        engine.configure_agents(
            model=GeminiStructuredAdapter(
                api_key=settings.gemini_api_key,
                model_name=settings.gemini_model,
            ),
            repository_revision=settings.repository_revision,
        )
        logger.info("Milestone 7 agents configured with model %s", settings.gemini_model)
    else:
        logger.warning(
            "GEMINI_API_KEY is not configured; agent processing is disabled and will fail closed"
        )
    await engine.run_loop()


if __name__ == "__main__":
    asyncio.run(main())
