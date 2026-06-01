from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.admin import Admin
from app.models.access_log import AccessLog
from app.auth.dependencies import get_current_admin

router = APIRouter(prefix="/access-logs", tags=["Access Logs"])


@router.get("")
async def list_logs(admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AccessLog)
        .where(AccessLog.gym_id == admin.gym_id)
        .order_by(AccessLog.scanned_at.desc())
        .limit(100)
    )
    return result.scalars().all()
