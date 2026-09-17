from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from typing import List

from app.dashboard.schemas import (
    DevOpsViewResponse,
    IncidentItem,
    KillSwitchRequest,
    KillSwitchResponse,
    ManagementViewResponse,
)
from app.dashboard.store import incidents_db, kill_switch_state
from app.auth import require_operator
from app.telemetry.client import clickhouse_client

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/devops", response_model=DevOpsViewResponse)
async def get_devops_view():
    active = [inc for inc in incidents_db.values() if inc.status not in ("Resolved", "Rolled back")]
    resolved = [inc for inc in incidents_db.values() if inc.status in ("Resolved", "Rolled back")]

    # Get recent telemetry count from ClickHouse
    try:
        tables = await clickhouse_client.get_tables()
        telemetry_summary = {"status": "connected", "table_count": len(tables)}
    except Exception:
        telemetry_summary = {"status": "disconnected", "table_count": 0}

    return DevOpsViewResponse(
        kill_switch_active=kill_switch_state["active"],
        active_incidents=active,
        resolved_incidents=resolved,
        recent_telemetry_summary=telemetry_summary,
    )


@router.get("/management", response_model=ManagementViewResponse)
async def get_management_view():
    total_incidents = len(incidents_db)
    resolved_count = len([inc for inc in incidents_db.values() if inc.status in ("Resolved", "Rolled back")])
    open_count = total_incidents - resolved_count

    return ManagementViewResponse(
        overall_health="UNKNOWN" if total_incidents == 0 else ("HEALTHY" if open_count == 0 and not kill_switch_state["active"] else "DEGRADED"),
        open_incidents_count=open_count,
        resolved_incidents_count=resolved_count,
        release_qualification_status="NOT RUN — no verified 72-execution qualification report",
    )


@router.post("/kill-switch", response_model=KillSwitchResponse)
async def set_kill_switch(body: KillSwitchRequest, _operator: str = Depends(require_operator)):
    kill_switch_state["active"] = body.active
    kill_switch_state["updated_at"] = datetime.now(timezone.utc)
    kill_switch_state["reason"] = body.reason

    state_str = "ACTIVATED (Automation Halted)" if body.active else "DEACTIVATED (Normal Operation)"

    # Mark active incidents as escalated if kill switch is activated per REQ-UI-03
    if body.active:
        for inc in incidents_db.values():
            if inc.status not in ("Resolved", "Rolled back"):
                inc.status = "Escalated"
                inc.audit_trail.append({
                    "event": "KILL_SWITCH_TRIGGERED",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "actor": "Operator",
                    "reason": body.reason,
                })

    return KillSwitchResponse(
        active=body.active,
        timestamp=kill_switch_state["updated_at"],
        message=f"Kill switch {state_str}. Reason: {body.reason}",
    )


@router.get("/incidents", response_model=List[IncidentItem])
async def list_incidents():
    return list(incidents_db.values())


@router.post("/incidents", response_model=IncidentItem)
async def create_incident(item: IncidentItem, _operator: str = Depends(require_operator)):
    incidents_db[item.id] = item
    return item
