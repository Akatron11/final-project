import uuid
from datetime import date, timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.admin import Admin
from app.models.member import Member
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.plan import MembershipPlan
from app.schemas.subscription import SubscriptionCreate
from app.auth.dependencies import get_current_admin

router = APIRouter(tags=["Subscriptions"])


@router.post("/members/{member_id}/subscriptions", status_code=201)
async def create_subscription(member_id: uuid.UUID, body: SubscriptionCreate, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    member_result = await db.execute(
        select(Member).where(Member.id == member_id, Member.gym_id == admin.gym_id)
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Member not found")

    plan_result = await db.execute(
        select(MembershipPlan).where(MembershipPlan.id == body.plan_id, MembershipPlan.gym_id == admin.gym_id)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    subscription = Subscription(
        gym_id=admin.gym_id,
        member_id=member_id,
        plan_id=body.plan_id,
        start_date=body.start_date,
        end_date=body.start_date + timedelta(days=plan.duration_days)
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription


@router.get("/members/{member_id}/subscriptions")
async def list_subscriptions(member_id: uuid.UUID, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subscription).where(
            Subscription.member_id == member_id,
            Subscription.gym_id == admin.gym_id
        ).order_by(Subscription.created_at.desc())
    )
    return result.scalars().all()


@router.put("/subscriptions/{sub_id}/freeze")
async def freeze(sub_id: uuid.UUID, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subscription).where(Subscription.id == sub_id, Subscription.gym_id == admin.gym_id)
    )
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
async def unfreeze(sub_id: uuid.UUID, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subscription).where(Subscription.id == sub_id, Subscription.gym_id == admin.gym_id)
    )
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
async def cancel(sub_id: uuid.UUID, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subscription).where(Subscription.id == sub_id, Subscription.gym_id == admin.gym_id)
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    subscription.status = SubscriptionStatus.suspended
    await db.commit()
    await db.refresh(subscription)
    return subscription
