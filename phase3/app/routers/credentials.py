import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.admin import Admin
from app.models.member import Member
from app.models.credential import Credential
from app.schemas.credential import NFCAssign
from app.auth.dependencies import get_current_admin
from app.utils.encryption import encrypt_payload
from app.utils.qr_generator import generate_qr_base64

router = APIRouter(tags=["Credentials"])


@router.post("/members/{member_id}/credentials/qr", status_code=201)
async def generate_qr(member_id: uuid.UUID, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.gym_id == admin.gym_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Member not found")

    old = await db.execute(
        select(Credential).where(
            Credential.member_id == member_id,
            Credential.gym_id == admin.gym_id,
            Credential.credential_type == "qr",
            Credential.is_active == True
        )
    )
    for c in old.scalars().all():
        c.is_active = False

    encrypted = encrypt_payload(str(admin.gym_id), str(member_id))

    credential = Credential(
        gym_id=admin.gym_id,
        member_id=member_id,
        credential_type="qr",
        credential_value=encrypted
    )
    db.add(credential)
    await db.commit()
    await db.refresh(credential)

    return {
        "credential_id": str(credential.id),
        "qr_base64": generate_qr_base64(encrypted),
        "message": "QR code generated"
    }


@router.post("/members/{member_id}/credentials/nfc", status_code=201)
async def assign_nfc(member_id: uuid.UUID, body: NFCAssign, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.gym_id == admin.gym_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Member not found")

    existing = await db.execute(
        select(Credential).where(
            Credential.gym_id == admin.gym_id,
            Credential.credential_value == body.nfc_tag_uid,
            Credential.credential_type == "nfc",
            Credential.is_active == True
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="NFC tag already assigned")

    credential = Credential(
        gym_id=admin.gym_id,
        member_id=member_id,
        credential_type="nfc",
        credential_value=body.nfc_tag_uid
    )
    db.add(credential)
    await db.commit()
    await db.refresh(credential)
    return {"credential_id": str(credential.id), "message": "NFC tag assigned"}


@router.get("/members/{member_id}/credentials")
async def list_credentials(member_id: uuid.UUID, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Credential).where(
            Credential.member_id == member_id,
            Credential.gym_id == admin.gym_id
        )
    )
    return result.scalars().all()


@router.delete("/credentials/{credential_id}", status_code=204)
async def revoke(credential_id: uuid.UUID, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Credential).where(Credential.id == credential_id, Credential.gym_id == admin.gym_id)
    )
    credential = result.scalar_one_or_none()
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    credential.is_active = False
    await db.commit()
