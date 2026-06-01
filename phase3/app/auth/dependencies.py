import uuid
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.auth.jwt_handler import decode_token
from app.database import get_db
from app.models.admin import Admin
from app.models.gate_device import GateDevice
from app.redis_client import get_redis

bearer_scheme = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> Admin:
    try:
        payload = decode_token(credentials.credentials)
        admin_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(
        select(Admin).where(Admin.id == uuid.UUID(admin_id), Admin.is_active == True)
    )
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")

    return admin


async def get_gate_device(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> GateDevice:
    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header is required")

    result = await db.execute(select(GateDevice).where(GateDevice.is_active == True))
    devices = result.scalars().all()

    for device in devices:
        if pwd_context.verify(api_key, device.api_key_hash):
            return device

    raise HTTPException(status_code=401, detail="Invalid API key")


async def check_rate_limit(device: GateDevice = Depends(get_gate_device)) -> GateDevice:
    """Allow max 60 verify requests per minute per gate device."""
    redis = get_redis()
    key = f"rate_limit:{device.id}:{int(__import__('time').time() // 60)}"

    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)

    if count > 60:
        raise HTTPException(status_code=429, detail="Rate limit exceeded: max 60 requests per minute")

    return device
