from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models.admin import Admin
from app.models.member import Member
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.access_log import AccessLog, AccessDecision
from app.auth.dependencies import get_current_admin

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
async def get_dashboard(
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    gym_id = admin.gym_id
    today = date.today()

    # Bugünün girişleri
    checkins_result = await db.execute(
        select(func.count(AccessLog.id)).where(
            AccessLog.gym_id == gym_id,
            AccessLog.decision == AccessDecision.GRANTED,
            AccessLog.action == "entry",
            func.date(AccessLog.scanned_at) == today
        )
    )
    todays_checkins = checkins_result.scalar() or 0

    # Aktif üye sayısı
    active_result = await db.execute(
        select(func.count(Member.id)).where(
            Member.gym_id == gym_id,
            Member.is_active == True
        )
    )
    active_members = active_result.scalar() or 0

    # 7 gün içinde üyeliği bitecekler
    in_7_days = today + timedelta(days=7)
    expiring_result = await db.execute(
        select(Member.id, Member.first_name, Member.last_name, Member.email, Subscription.end_date)
        .join(Subscription, and_(
            Subscription.member_id == Member.id,
            Subscription.gym_id == gym_id
        ))
        .where(
            Member.gym_id == gym_id,
            Member.is_active == True,
            Subscription.status == SubscriptionStatus.active,
            Subscription.end_date >= today,
            Subscription.end_date <= in_7_days
        )
    )
    expiring_soon = [
        {
            "member_id": str(row.id),
            "name": f"{row.first_name} {row.last_name}",
            "email": row.email,
            "expires_on": row.end_date.isoformat()
        }
        for row in expiring_result.all()
    ]

    # 30+ gün hiç gelmemiş aktif üyeler
    cutoff = today - timedelta(days=30)
    last_visit_sub = (
        select(
            AccessLog.member_id,
            func.max(AccessLog.scanned_at).label("last_visit")
        )
        .where(
            AccessLog.gym_id == gym_id,
            AccessLog.decision == AccessDecision.GRANTED
        )
        .group_by(AccessLog.member_id)
        .subquery()
    )

    inactive_result = await db.execute(
        select(Member.id, Member.first_name, Member.last_name, Member.email, last_visit_sub.c.last_visit)
        .outerjoin(last_visit_sub, last_visit_sub.c.member_id == Member.id)
        .where(
            Member.gym_id == gym_id,
            Member.is_active == True,
            (last_visit_sub.c.last_visit == None) | (func.date(last_visit_sub.c.last_visit) < cutoff)
        )
    )
    inactive_members = [
        {
            "member_id": str(row.id),
            "name": f"{row.first_name} {row.last_name}",
            "email": row.email,
            "last_visit": row.last_visit.date().isoformat() if row.last_visit else None
        }
        for row in inactive_result.all()
    ]

    return {
        "todays_checkins": todays_checkins,
        "active_member_count": active_members,
        "expiring_within_7_days": expiring_soon,
        "inactive_30_days": inactive_members
    }
