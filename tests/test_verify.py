import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_verify_missing_api_key(client: AsyncClient):
    resp = await client.post("/api/v1/verify", json={
        "credential_type": "qr",
        "credential_value": "invalid",
        "gate_id": "GATE-A",
        "action": "entry"
    })
    assert resp.status_code == 403


async def test_verify_invalid_api_key(client: AsyncClient):
    resp = await client.post(
        "/api/v1/verify",
        headers={"X-API-Key": "wrong-key"},
        json={
            "credential_type": "qr",
            "credential_value": "invalid",
            "gate_id": "GATE-A",
            "action": "entry"
        }
    )
    assert resp.status_code == 401


async def test_auth_register_and_login(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "gym_name": "TestGym",
        "gym_address": "Istanbul",
        "gym_phone": "+905550000001",
        "gym_email": "test@testgym.com",
        "gym_max_capacity": 50,
        "admin_email": "admin@testgym.com",
        "admin_password": "Test1234!",
        "admin_full_name": "Test Admin"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "gym_id" in data

    login = await client.post("/api/v1/auth/login", json={
        "email": "admin@testgym.com",
        "password": "Test1234!"
    })
    assert login.status_code == 200
    assert "access_token" in login.json()


async def test_dashboard_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/dashboard")
    assert resp.status_code in (401, 403)
