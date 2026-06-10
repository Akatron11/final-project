import pytest
from httpx import AsyncClient

from app.models.subscription import SubscriptionStatus

pytestmark = pytest.mark.asyncio


async def verify(client: AsyncClient, api_key: str, credential_value: str):
    return await client.post(
        "/api/v1/verify",
        headers={"X-API-Key": api_key},
        json={
            "credential_type": "nfc",
            "credential_value": credential_value,
            "gate_id": "GATE-A",
            "action": "entry",
        },
    )


async def test_rate_limit_blocks_after_60_requests(client: AsyncClient, seed, make_member):
    _, credential_value = await make_member(seed, status=SubscriptionStatus.active)

    for _ in range(60):
        resp = await verify(client, seed["api_key"], credential_value)
        assert resp.status_code == 200

    resp = await verify(client, seed["api_key"], credential_value)
    assert resp.status_code == 429


async def test_tenant_isolation_other_gym_credential_is_unknown(client: AsyncClient, seed, make_gym, make_member):
    other_gym = await make_gym(name="OtherGym")
    _, other_credential_value = await make_member(other_gym, status=SubscriptionStatus.active)

    resp = await verify(client, seed["api_key"], other_credential_value)

    assert resp.status_code == 200
    assert resp.json()["decision"] == "DENIED_UNKNOWN"
