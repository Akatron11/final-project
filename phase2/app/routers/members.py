import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.member import Member

router = APIRouter(prefix="/members", tags=["Members"])


@router.get("")
async def list_members(gym_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Member).where(Member.gym_id == gym_id))
    members = result.scalars().all()
    return members


@router.post("", status_code=201)
async def create_member(body: dict, db: AsyncSession = Depends(get_db)):
    member = Member(
        gym_id=body["gym_id"],
        first_name=body["first_name"],
        last_name=body["last_name"],
        email=body["email"],
        phone=body.get("phone"),
        date_of_birth=body.get("date_of_birth"),
        emergency_contact=body.get("emergency_contact")
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.get("/{member_id}")
async def get_member(member_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.put("/{member_id}")
async def update_member(member_id: uuid.UUID, body: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    for field in ["first_name", "last_name", "phone", "emergency_contact", "photo_url"]:
        if field in body:
            setattr(member, field, body[field])

    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=204)
async def deactivate_member(member_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.is_active = False
    await db.commit()


@router.post("/{member_id}/flag")
async def flag_member(member_id: uuid.UUID, body: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.is_flagged = True
    member.flag_reason = body["reason"]
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{member_id}/flag")
async def unflag_member(member_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.is_flagged = False
    member.flag_reason = None
    await db.commit()
    await db.refresh(member)
    return member
