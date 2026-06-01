import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.plan import MembershipPlan

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("")
async def list_plans(gym_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MembershipPlan).where(MembershipPlan.gym_id == gym_id))
    return result.scalars().all()


@router.post("", status_code=201)
async def create_plan(body: dict, db: AsyncSession = Depends(get_db)):
    plan = MembershipPlan(
        gym_id=body["gym_id"],
        name=body["name"],
        description=body.get("description"),
        duration_days=body["duration_days"],
        price=body["price"],
        max_freezes=body.get("max_freezes", 1)
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.put("/{plan_id}")
async def update_plan(plan_id: uuid.UUID, body: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    for field in ["name", "description", "duration_days", "price", "max_freezes"]:
        if field in body:
            setattr(plan, field, body[field])

    await db.commit()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_id}", status_code=204)
async def deactivate_plan(plan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MembershipPlan).where(MembershipPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.is_active = False
    await db.commit()
