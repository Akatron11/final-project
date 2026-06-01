from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import settings

ALGORITHM = "HS256"
EXPIRE_MINUTES = 60


def create_token(admin_id: str, gym_id: str) -> str:
    payload = {
        "sub": admin_id,
        "gym_id": gym_id,
        "role": "gym_admin",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
