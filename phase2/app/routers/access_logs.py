import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.access_log import AccessLog

router = APIRouter(prefix="/access-logs", tags=["Access Logs"])


@router.get("")
async def list_logs(gym_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AccessLog)
        .where(AccessLog.gym_id == gym_id)
        .order_by(AccessLog.scanned_at.desc())
        .limit(100)
    )
    return result.scalars().all()
