from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from app.models.credential import Credential
from app.models.subscription import SubscriptionStatus
from app.utils.encryption import encrypt_payload

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


async def test_denied_already_inside(client: AsyncClient, seed, make_member):
    _, credential_value = await make_member(seed, status=SubscriptionStatus.active)

    resp = await verify(client, seed["api_key"], credential_value, action="entry")
    assert resp.json()["decision"] == "GRANTED"

    resp = await verify(client, seed["api_key"], credential_value, action="entry")
    assert resp.status_code == 200
    assert resp.json()["decision"] == "DENIED_ALREADY_INSIDE"


async def test_old_qr_denied_after_regenerating(client: AsyncClient, seed, make_member, db):
    member, _ = await make_member(seed, status=SubscriptionStatus.active)

    old_qr = encrypt_payload(str(seed["gym"].id), str(member.id))
    old_credential = Credential(
        gym_id=seed["gym"].id,
        member_id=member.id,
        credential_type="qr",
        credential_value=old_qr,
    )
    db.add(old_credential)
    await db.flush()

    # Simulate generating a new QR: old one is deactivated, a new active one is added
    old_credential.is_active = False
    new_qr = encrypt_payload(str(seed["gym"].id), str(member.id))
    db.add(Credential(
        gym_id=seed["gym"].id,
        member_id=member.id,
        credential_type="qr",
        credential_value=new_qr,
    ))
    await db.commit()

    resp = await client.post(
        "/api/v1/verify",
        headers={"X-API-Key": seed["api_key"]},
        json={
            "credential_type": "qr",
            "credential_value": old_qr,
            "gate_id": "GATE-A",
            "action": "entry",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["decision"] == "DENIED_UNKNOWN"


async def test_exit_after_entry_then_denied_not_inside(client: AsyncClient, seed, make_member):
    _, credential_value = await make_member(seed, status=SubscriptionStatus.active)

    resp = await verify(client, seed["api_key"], credential_value, action="entry")
    assert resp.json()["decision"] == "GRANTED"

    resp = await verify(client, seed["api_key"], credential_value, action="exit")
    assert resp.json()["decision"] == "GRANTED"

    resp = await verify(client, seed["api_key"], credential_value, action="exit")
    assert resp.status_code == 200
    assert resp.json()["decision"] == "DENIED_NOT_INSIDE"
