from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.gate_device import GateDevice
from app.schemas.verify import VerifyRequest
from app.auth.dependencies import check_rate_limit
from app.services.verification import run_verification

router = APIRouter(tags=["Verify"])


@router.post("/verify")
async def verify(
    body: VerifyRequest,
    device: GateDevice = Depends(check_rate_limit),
    db: AsyncSession = Depends(get_db)
):
    return await run_verification(body.model_dump(), device, db)
