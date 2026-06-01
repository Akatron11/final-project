"""
Entry Verification Engine

Accepts a scanned QR payload or NFC tag ID and returns an access decision.
Every scan is logged to access_logs.
The Redis occupancy counter is incremented on entry and decremented on exit.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.access_log import AccessLog, AccessDecision
from app.models.credential import Credential
from app.models.member import Member
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.gym import Gym
from app.models.gate_device import GateDevice
from app.utils.encryption import decrypt_payload
from app.redis_client import get_redis


async def run_verification(body: dict, db: AsyncSession) -> dict:
    credential_type = body["credential_type"]
    credential_value = body["credential_value"]
    gate_id = body["gate_id"]
    action = body.get("action", "entry")
    now = datetime.now(timezone.utc)

    # Find the gate device to get the gym_id
    result = await db.execute(
        select(GateDevice).where(GateDevice.api_key == body["api_key"], GateDevice.is_active == True)
    )
    device = result.scalar_one_or_none()
    if not device:
        return {"decision": "DENIED_UNKNOWN", "scanned_at": now}

    gym_id = device.gym_id

    async def write_log(decision, member_id=None, is_flag_log=False):
        log = AccessLog(
            gym_id=gym_id,
            member_id=member_id,
            gate_id=gate_id,
            credential_type=credential_type,
            action=action,
            decision=decision,
            is_flag_log=is_flag_log
        )
        db.add(log)
        await db.commit()

    # Step 1: Resolve the credential

    if credential_type == "qr":
        try:
            payload = decrypt_payload(credential_value)
        except Exception:
            await write_log(AccessDecision.DENIED_UNKNOWN)
            return {"decision": "DENIED_UNKNOWN", "scanned_at": now}

        # Tenant isolation: QR must belong to this gym
        if str(gym_id) != payload.get("gym_id"):
            await write_log(AccessDecision.DENIED_UNKNOWN)
            return {"decision": "DENIED_UNKNOWN", "scanned_at": now}

        member_id = uuid.UUID(payload["member_id"])

        result = await db.execute(
            select(Credential).where(
                Credential.member_id == member_id,
                Credential.gym_id == gym_id,
                Credential.credential_type == "qr",
                Credential.is_active == True
            )
        )
        credential = result.scalar_one_or_none()

    else:
        # NFC: match raw UID within this gym only
        result = await db.execute(
            select(Credential).where(
                Credential.credential_value == credential_value,
                Credential.gym_id == gym_id,
                Credential.credential_type == "nfc",
                Credential.is_active == True
            )
        )
        credential = result.scalar_one_or_none()
        if not credential:
            await write_log(AccessDecision.DENIED_UNKNOWN)
            return {"decision": "DENIED_UNKNOWN", "scanned_at": now}
        member_id = credential.member_id

    if not credential:
        await write_log(AccessDecision.DENIED_UNKNOWN)
        return {"decision": "DENIED_UNKNOWN", "scanned_at": now}

    # Step 2: Load the member

    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.gym_id == gym_id)
    )
    member = result.scalar_one_or_none()

    if not member or not member.is_active:
        await write_log(AccessDecision.DENIED_UNKNOWN, member_id=member_id)
        return {"decision": "DENIED_UNKNOWN", "scanned_at": now}

    # Step 3: Flagged members — no personal details in the response

    if member.is_flagged:
        await write_log(AccessDecision.DENIED_FLAGGED, member_id=member_id, is_flag_log=True)
        return {
            "decision": "DENIED_FLAGGED",
            "flag_reason": member.flag_reason,
            "scanned_at": now
        }

    # Step 4: Check subscription

    result = await db.execute(
        select(Subscription).where(
            Subscription.member_id == member_id,
            Subscription.gym_id == gym_id
        ).order_by(Subscription.created_at.desc())
    )
    subscription = result.scalars().first()

    if not subscription:
        await write_log(AccessDecision.DENIED_UNKNOWN, member_id=member_id)
        return {"decision": "DENIED_UNKNOWN", "scanned_at": now}

    if subscription.status == SubscriptionStatus.active and subscription.end_date < date.today():
        subscription.status = SubscriptionStatus.expired
        await db.commit()

    if subscription.status == SubscriptionStatus.expired:
        await write_log(AccessDecision.DENIED_EXPIRED, member_id=member_id)
        return {"decision": "DENIED_EXPIRED", "scanned_at": now}

    if subscription.status == SubscriptionStatus.suspended:
        await write_log(AccessDecision.DENIED_SUSPENDED, member_id=member_id)
        return {"decision": "DENIED_SUSPENDED", "scanned_at": now}

    if subscription.status == SubscriptionStatus.frozen:
        await write_log(AccessDecision.DENIED_FROZEN, member_id=member_id)
        return {"decision": "DENIED_FROZEN", "scanned_at": now}

    # Step 5: GRANTED — update Redis occupancy counter

    redis = get_redis()
    key = f"gym:{gym_id}:occupancy"

    if action == "entry":
        occupancy = await redis.incr(key)
    else:
        current = await redis.get(key)
        occupancy = max(0, int(current or 0) - 1)
        await redis.set(key, occupancy)

    # Visits this month
    today = date.today()
    visit_result = await db.execute(
        select(func.count(AccessLog.id)).where(
            AccessLog.member_id == member_id,
            AccessLog.gym_id == gym_id,
            AccessLog.decision == AccessDecision.GRANTED,
            AccessLog.action == "entry",
            func.extract("month", AccessLog.scanned_at) == today.month,
            func.extract("year", AccessLog.scanned_at) == today.year,
        )
    )
    visits_this_month = (visit_result.scalar() or 0) + 1

    gym_result = await db.execute(select(Gym).where(Gym.id == gym_id))
    gym = gym_result.scalar_one_or_none()

    await write_log(AccessDecision.GRANTED, member_id=member_id)

    return {
        "decision": "GRANTED",
        "member": {
            "id": str(member.id),
            "name": f"{member.first_name} {member.last_name}",
            "membership_tier": subscription.plan.name if subscription.plan else "Standard",
            "photo_url": member.photo_url,
            "visits_this_month": visits_this_month
        },
        "gym_id": str(gym_id),
        "gate_id": gate_id,
        "credential_type": credential_type,
        "gym_occupancy": {
            "current": occupancy,
            "max": gym.max_capacity if gym else 0
        },
        "scanned_at": now
    }
