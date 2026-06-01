import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.gate_device import GateDevice

router = APIRouter(prefix="/devices", tags=["Gate Devices"])


@router.get("")
async def list_devices(gym_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GateDevice).where(GateDevice.gym_id == gym_id))
    return result.scalars().all()


@router.post("", status_code=201)
async def create_device(body: dict, db: AsyncSession = Depends(get_db)):
    api_key = secrets.token_urlsafe(32)
    device = GateDevice(
        gym_id=body["gym_id"],
        name=body["name"],
        api_key=api_key
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return {
        "id": str(device.id),
        "name": device.name,
        "api_key": api_key,
        "note": "Save this key — it will not be shown again"
    }


@router.delete("/{device_id}", status_code=204)
async def deactivate_device(device_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GateDevice).where(GateDevice.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.is_active = False
    await db.commit()
