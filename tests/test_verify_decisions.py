from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from app.models.subscription import SubscriptionStatus

pytestmark = pytest.mark.asyncio


async def verify(client: AsyncClient, api_key: str, credential_value: str, action: str = "entry"):
    return await client.post(
        "/api/v1/verify",
        headers={"X-API-Key": api_key},
        json={
            "credential_type": "nfc",
            "credential_value": credential_value,
            "gate_id": "GATE-A",
            "action": action,
        },
    )


async def test_granted(client: AsyncClient, seed, make_member):
    _, credential_value = await make_member(seed, status=SubscriptionStatus.active)

    resp = await verify(client, seed["api_key"], credential_value)

    assert resp.status_code == 200
    assert resp.json()["decision"] == "GRANTED"


async def test_denied_unknown_credential(client: AsyncClient, seed):
    resp = await verify(client, seed["api_key"], "does-not-exist")

    assert resp.status_code == 200
    assert resp.json()["decision"] == "DENIED_UNKNOWN"


async def test_denied_flagged(client: AsyncClient, seed, make_member):
    _, credential_value = await make_member(seed, is_flagged=True, flag_reason="Stolen card")

    resp = await verify(client, seed["api_key"], credential_value)

    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "DENIED_FLAGGED"
    assert body["flag_reason"] == "Stolen card"
    assert "member" not in body


async def test_denied_expired(client: AsyncClient, seed, make_member):
    _, credential_value = await make_member(
        seed,
        status=SubscriptionStatus.active,
        end_date=date.today() - timedelta(days=1),
    )

    resp = await verify(client, seed["api_key"], credential_value)

    assert resp.status_code == 200
    assert resp.json()["decision"] == "DENIED_EXPIRED"


async def test_denied_suspended(client: AsyncClient, seed, make_member):
    _, credential_value = await make_member(seed, status=SubscriptionStatus.suspended)

    resp = await verify(client, seed["api_key"], credential_value)

    assert resp.status_code == 200
    assert resp.json()["decision"] == "DENIED_SUSPENDED"


async def test_denied_frozen(client: AsyncClient, seed, make_member):
    _, credential_value = await make_member(seed, status=SubscriptionStatus.frozen)

    resp = await verify(client, seed["api_key"], credential_value)

    assert resp.status_code == 200
    assert resp.json()["decision"] == "DENIED_FROZEN"
