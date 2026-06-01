from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.verification import run_verification

router = APIRouter(tags=["Verify"])


@router.post("/verify")
async def verify(body: dict, db: AsyncSession = Depends(get_db)):
    return await run_verification(body, db)
