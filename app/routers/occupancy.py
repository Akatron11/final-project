from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.admin import Admin
from app.models.gym import Gym
from app.auth.dependencies import get_current_admin
from app.redis_client import get_redis

router = APIRouter(prefix="/occupancy", tags=["Occupancy"])


@router.get("")
async def get_occupancy(admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    redis = get_redis()
    current = await redis.get(f"gym:{admin.gym_id}:occupancy")
    current_count = int(current) if current else 0

    result = await db.execute(select(Gym).where(Gym.id == admin.gym_id))
    gym = result.scalar_one_or_none()
    max_capacity = gym.max_capacity if gym else 0

    return {
        "current_occupancy": current_count,
        "max_capacity": max_capacity,
        "utilization_percentage": round(current_count / max_capacity * 100, 1) if max_capacity > 0 else 0.0
    }
