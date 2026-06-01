import uuid
from datetime import date, timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.plan import MembershipPlan

router = APIRouter(tags=["Subscriptions"])


@router.post("/members/{member_id}/subscriptions", status_code=201)
async def create_subscription(member_id: uuid.UUID, body: dict, db: AsyncSession = Depends(get_db)):
    plan_result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == body["plan_id"]))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    start = date.fromisoformat(body["start_date"])
    end = start + timedelta(days=plan.duration_days)

    subscription = Subscription(
        gym_id=body["gym_id"],
        member_id=member_id,
        plan_id=body["plan_id"],
        start_date=start,
        end_date=end
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription


@router.get("/members/{member_id}/subscriptions")
async def list_subscriptions(member_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subscription).where(Subscription.member_id == member_id)
        .order_by(Subscription.created_at.desc())
    )
    return result.scalars().all()


@router.put("/subscriptions/{sub_id}/freeze")
async def freeze(sub_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscription).where(Subscription.id == sub_id))
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if subscription.status != SubscriptionStatus.active:
        raise HTTPException(status_code=400, detail="Only active subscriptions can be frozen")

    plan_result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == subscription.plan_id))
    plan = plan_result.scalar_one_or_none()
    if plan and subscription.freeze_count >= plan.max_freezes:
        raise HTTPException(status_code=400, detail="Freeze limit reached")

    subscription.status = SubscriptionStatus.frozen
    subscription.frozen_at = datetime.now(timezone.utc)
    subscription.freeze_count += 1
    await db.commit()
    await db.refresh(subscription)
    return subscription


@router.put("/subscriptions/{sub_id}/unfreeze")
async def unfreeze(sub_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscription).where(Subscription.id == sub_id))
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if subscription.status != SubscriptionStatus.frozen:
        raise HTTPException(status_code=400, detail="Subscription is not frozen")

    if subscription.frozen_at:
        frozen_days = (date.today() - subscription.frozen_at.date()).days
        subscription.end_date = subscription.end_date + timedelta(days=frozen_days)

    subscription.status = SubscriptionStatus.active
    subscription.frozen_at = None
    await db.commit()
    await db.refresh(subscription)
    return subscription


@router.put("/subscriptions/{sub_id}/cancel")
async def cancel(sub_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscription).where(Subscription.id == sub_id))
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    subscription.status = SubscriptionStatus.suspended
    await db.commit()
    await db.refresh(subscription)
    return subscription
