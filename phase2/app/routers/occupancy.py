import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.gym import Gym
from app.redis_client import get_redis

router = APIRouter(prefix="/occupancy", tags=["Occupancy"])


@router.get("")
async def get_occupancy(gym_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    redis = get_redis()
    key = f"gym:{gym_id}:occupancy"
    current = await redis.get(key)
    current_count = int(current) if current else 0

    result = await db.execute(select(Gym).where(Gym.id == gym_id))
    gym = result.scalar_one_or_none()
    max_capacity = gym.max_capacity if gym else 0

    return {
        "current_occupancy": current_count,
        "max_capacity": max_capacity,
        "utilization_percentage": round(current_count / max_capacity * 100, 1) if max_capacity > 0 else 0.0
    }
