import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.admin import Admin
from app.models.plan import MembershipPlan
from app.schemas.plan import PlanCreate, PlanUpdate
from app.auth.dependencies import get_current_admin

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("")
async def list_plans(admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MembershipPlan).where(MembershipPlan.gym_id == admin.gym_id))
    return result.scalars().all()


@router.post("", status_code=201)
async def create_plan(body: PlanCreate, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    plan = MembershipPlan(gym_id=admin.gym_id, **body.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.put("/{plan_id}")
async def update_plan(plan_id: uuid.UUID, body: PlanUpdate, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MembershipPlan).where(MembershipPlan.id == plan_id, MembershipPlan.gym_id == admin.gym_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(plan, field, value)

    await db.commit()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_id}", status_code=204)
async def deactivate_plan(plan_id: uuid.UUID, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MembershipPlan).where(MembershipPlan.id == plan_id, MembershipPlan.gym_id == admin.gym_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.is_active = False
    await db.commit()
