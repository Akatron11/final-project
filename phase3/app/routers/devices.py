import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.admin import Admin
from app.models.gate_device import GateDevice
from app.schemas.device import DeviceCreate
from app.auth.dependencies import get_current_admin

router = APIRouter(prefix="/devices", tags=["Gate Devices"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("")
async def list_devices(admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GateDevice).where(GateDevice.gym_id == admin.gym_id))
    devices = result.scalars().all()
    return [{"id": str(d.id), "name": d.name, "is_active": d.is_active} for d in devices]


@router.post("", status_code=201)
async def create_device(body: DeviceCreate, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    raw_key = secrets.token_urlsafe(32)
    device = GateDevice(
        gym_id=admin.gym_id,
        name=body.name,
        api_key_hash=pwd_context.hash(raw_key)
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return {
        "id": str(device.id),
        "name": device.name,
        "api_key": raw_key,
        "note": "Save this key — it will not be shown again"
    }


@router.delete("/{device_id}", status_code=204)
async def deactivate_device(device_id: uuid.UUID, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GateDevice).where(GateDevice.id == device_id, GateDevice.gym_id == admin.gym_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.is_active = False
    await db.commit()
