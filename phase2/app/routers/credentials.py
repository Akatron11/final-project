import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.credential import Credential
from app.utils.encryption import encrypt_payload
from app.utils.qr_generator import generate_qr_base64

router = APIRouter(tags=["Credentials"])


@router.post("/members/{member_id}/credentials/qr", status_code=201)
async def generate_qr(member_id: uuid.UUID, body: dict, db: AsyncSession = Depends(get_db)):
    gym_id = body["gym_id"]

    # Revoke existing QR credentials for this member
    old = await db.execute(
        select(Credential).where(
            Credential.member_id == member_id,
            Credential.gym_id == gym_id,
            Credential.credential_type == "qr",
            Credential.is_active == True
        )
    )
    for c in old.scalars().all():
        c.is_active = False

    # Encrypt gym_id + member_id so QR only works at this gym
    encrypted = encrypt_payload(str(gym_id), str(member_id))

    credential = Credential(
        gym_id=gym_id,
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
async def assign_nfc(member_id: uuid.UUID, body: dict, db: AsyncSession = Depends(get_db)):
    gym_id = body["gym_id"]
    nfc_uid = body["nfc_tag_uid"]

    existing = await db.execute(
        select(Credential).where(
            Credential.gym_id == gym_id,
            Credential.credential_value == nfc_uid,
            Credential.credential_type == "nfc",
            Credential.is_active == True
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="NFC tag already assigned")

    credential = Credential(
        gym_id=gym_id,
        member_id=member_id,
        credential_type="nfc",
        credential_value=nfc_uid
    )
    db.add(credential)
    await db.commit()
    await db.refresh(credential)
    return {"credential_id": str(credential.id), "message": "NFC tag assigned"}


@router.get("/members/{member_id}/credentials")
async def list_credentials(member_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Credential).where(Credential.member_id == member_id))
    return result.scalars().all()


@router.delete("/credentials/{credential_id}", status_code=204)
async def revoke(credential_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Credential).where(Credential.id == credential_id))
    credential = result.scalar_one_or_none()
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    credential.is_active = False
    await db.commit()
