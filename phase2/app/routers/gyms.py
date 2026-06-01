import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.gym import Gym

router = APIRouter(prefix="/gyms", tags=["Gyms"])


@router.post("", status_code=201)
async def create_gym(body: dict, db: AsyncSession = Depends(get_db)):
    gym = Gym(
        name=body["name"],
        address=body["address"],
        phone=body.get("phone"),
        email=body["email"],
        max_capacity=body.get("max_capacity", 100)
    )
    db.add(gym)
    await db.commit()
    await db.refresh(gym)
    return {"id": str(gym.id), "name": gym.name, "email": gym.email}


@router.get("/{gym_id}")
async def get_gym(gym_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Gym).where(Gym.id == gym_id))
    gym = result.scalar_one_or_none()
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    return gym


@router.put("/{gym_id}")
async def update_gym(gym_id: uuid.UUID, body: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Gym).where(Gym.id == gym_id))
    gym = result.scalar_one_or_none()
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")

    for field in ["name", "address", "phone", "max_capacity"]:
        if field in body:
            setattr(gym, field, body[field])

    await db.commit()
    await db.refresh(gym)
    return gym
