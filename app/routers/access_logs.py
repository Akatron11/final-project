import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.admin import Admin
from app.models.access_log import AccessLog, AccessDecision
from app.auth.dependencies import get_current_admin

router = APIRouter(prefix="/access-logs", tags=["Access Logs"])


@router.get("")
async def list_logs(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    member_id: Optional[uuid.UUID] = Query(None),
    decision: Optional[AccessDecision] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(AccessLog)
        .where(AccessLog.gym_id == admin.gym_id)
        .order_by(AccessLog.scanned_at.desc())
        .limit(limit)
    )

    if date_from:
        query = query.where(AccessLog.scanned_at >= date_from)
    if date_to:
        query = query.where(AccessLog.scanned_at <= date_to)
    if member_id:
        query = query.where(AccessLog.member_id == member_id)
    if decision:
        query = query.where(AccessLog.decision == decision)

    result = await db.execute(query)
    return result.scalars().all()
