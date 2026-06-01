from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.database import get_db
from app.models.gym import Gym
from app.models.admin import Admin
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.auth.jwt_handler import create_token

router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Gym).where(Gym.email == body.gym_email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A gym with this email already exists")

    gym = Gym(
        name=body.gym_name,
        address=body.gym_address,
        phone=body.gym_phone,
        email=body.gym_email,
        max_capacity=body.gym_max_capacity
    )
    db.add(gym)
    await db.flush()

    admin = Admin(
        gym_id=gym.id,
        email=body.admin_email,
        password_hash=pwd_context.hash(body.admin_password),
        full_name=body.admin_full_name
    )
    db.add(admin)
    await db.commit()

    return {"gym_id": str(gym.id), "admin_id": str(admin.id), "message": "Gym and admin created"}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Admin).where(Admin.email == body.email, Admin.is_active == True)
    )
    admin = result.scalar_one_or_none()

    if not admin or not pwd_context.verify(body.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(str(admin.id), str(admin.gym_id))
    return TokenResponse(access_token=token, gym_id=str(admin.gym_id))
