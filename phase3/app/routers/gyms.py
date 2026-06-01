from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta

from app.database import get_db
from app.models.gym import Gym
from app.models.admin import Admin
from app.models.member import Member
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.access_log import AccessLog, AccessDecision
from app.schemas.gym import GymUpdate
from app.auth.dependencies import get_current_admin

router = APIRouter(prefix="/gyms", tags=["Gyms"])


@router.get("/me")
async def get_my_gym(admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Gym).where(Gym.id == admin.gym_id))
    gym = result.scalar_one_or_none()
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    return gym


@router.put("/me")
async def update_gym(body: GymUpdate, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Gym).where(Gym.id == admin.gym_id))
    gym = result.scalar_one_or_none()

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(gym, field, value)

    await db.commit()
    await db.refresh(gym)
    return gym


@router.get("/me/dashboard")
async def dashboard(admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    today = date.today()

    checkins_result = await db.execute(
        select(func.count(AccessLog.id)).where(
            AccessLog.gym_id == admin.gym_id,
            AccessLog.decision == AccessDecision.GRANTED,
            AccessLog.action == "entry",
            func.date(AccessLog.scanned_at) == today
        )
    )
    todays_checkins = checkins_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(Member.id)).where(
            Member.gym_id == admin.gym_id,
            Member.is_active == True
        )
    )
    active_members = active_result.scalar() or 0

    in_7_days = today + timedelta(days=7)
    expiring_result = await db.execute(
        select(Subscription).where(
            Subscription.gym_id == admin.gym_id,
            Subscription.status == SubscriptionStatus.active,
            Subscription.end_date >= today,
            Subscription.end_date <= in_7_days
        )
    )
    expiring = expiring_result.scalars().all()

    thirty_days_ago = today - timedelta(days=30)
    recent_visitors = select(AccessLog.member_id).where(
        AccessLog.gym_id == admin.gym_id,
        AccessLog.decision == AccessDecision.GRANTED,
        func.date(AccessLog.scanned_at) >= thirty_days_ago
    ).distinct()

    inactive_result = await db.execute(
        select(Member).where(
            Member.gym_id == admin.gym_id,
            Member.is_active == True,
            Member.id.not_in(recent_visitors)
        )
    )
    inactive_members = inactive_result.scalars().all()

    return {
        "todays_checkins": todays_checkins,
        "active_member_count": active_members,
        "expiring_within_7_days": [str(s.member_id) for s in expiring],
        "not_visited_in_30_days": [str(m.id) for m in inactive_members]
    }
