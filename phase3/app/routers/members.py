import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.admin import Admin
from app.models.member import Member
from app.schemas.member import MemberCreate, MemberUpdate, FlagRequest
from app.auth.dependencies import get_current_admin

router = APIRouter(prefix="/members", tags=["Members"])


@router.get("")
async def list_members(admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Member).where(Member.gym_id == admin.gym_id))
    return result.scalars().all()


@router.post("", status_code=201)
async def create_member(body: MemberCreate, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    member = Member(gym_id=admin.gym_id, **body.model_dump())
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.get("/{member_id}")
async def get_member(member_id: uuid.UUID, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.gym_id == admin.gym_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.put("/{member_id}")
async def update_member(member_id: uuid.UUID, body: MemberUpdate, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.gym_id == admin.gym_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(member, field, value)

    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=204)
async def deactivate_member(member_id: uuid.UUID, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.gym_id == admin.gym_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.is_active = False
    await db.commit()


@router.post("/{member_id}/flag")
async def flag_member(member_id: uuid.UUID, body: FlagRequest, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.gym_id == admin.gym_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.is_flagged = True
    member.flag_reason = body.reason
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{member_id}/flag")
async def unflag_member(member_id: uuid.UUID, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.gym_id == admin.gym_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.is_flagged = False
    member.flag_reason = None
    await db.commit()
    await db.refresh(member)
    return member
