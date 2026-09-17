import os

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {os.environ.get('OPERATOR_TOKEN', 'test-operator-token')}"}


def test_get_devops_view():
    response = client.get("/api/v1/dashboard/devops")
    assert response.status_code == 200
    data = response.json()
    assert "kill_switch_active" in data
    assert "active_incidents" in data
    assert "resolved_incidents" in data


def test_get_management_view():
    response = client.get("/api/v1/dashboard/management")
    assert response.status_code == 200
    data = response.json()
    assert "overall_health" in data
    assert "remediation_success_rate_percent" in data
    assert "mean_recovery_seconds" in data


def test_kill_switch_activation():
    unauthorized = client.post(
        "/api/v1/dashboard/kill-switch",
        json={"active": True, "reason": "Missing credentials"},
    )
    assert unauthorized.status_code == 401

    # Activate kill switch
    response = client.post(
        "/api/v1/dashboard/kill-switch",
        json={"active": True, "reason": "Test emergency stop"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["active"] is True
    assert "ACTIVATED" in data["message"]

    # Verify DevOps view reflects active kill switch
    devops = client.get("/api/v1/dashboard/devops").json()
    assert devops["kill_switch_active"] is True

    # Deactivate kill switch
    response = client.post(
        "/api/v1/dashboard/kill-switch",
        json={"active": False, "reason": "Test reset"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["active"] is False
