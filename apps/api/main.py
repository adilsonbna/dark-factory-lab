from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.dashboard.router import router as dashboard_router
from app.mcp.router import router as mcp_router
from app.telemetry.router import router as telemetry_router

app = FastAPI(
    title="dark-factory-lab API",
    description="Control plane backend providing auth, ClickStack MCP bridge, GitHub integration, and audit services.",
    version="0.1.0",
)

app.include_router(telemetry_router)
app.include_router(mcp_router)
app.include_router(dashboard_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/incident")
async def get_incidents():
    return {"incidents": []}


FastAPIInstrumentor.instrument_app(app)
