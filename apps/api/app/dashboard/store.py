from datetime import datetime, timezone
from typing import Dict
from app.dashboard.schemas import IncidentItem

# Global state for Kill Switch and Incidents
kill_switch_state: Dict = {
    "active": False,
    "updated_at": datetime.now(timezone.utc),
    "reason": None,
}

# Runtime data starts empty. Incidents must come from real detector/orchestrator input;
# the dashboard must never present fixtures as operational evidence.
incidents_db: Dict[str, IncidentItem] = {}
