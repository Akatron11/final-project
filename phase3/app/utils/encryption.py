import json
from cryptography.fernet import Fernet
from app.config import settings


def get_fernet():
    return Fernet(settings.FERNET_KEY.encode())


def encrypt_payload(gym_id: str, member_id: str) -> str:
    data = json.dumps({"gym_id": gym_id, "member_id": member_id})
    return get_fernet().encrypt(data.encode()).decode()


def decrypt_payload(token: str) -> dict:
    raw = get_fernet().decrypt(token.encode())
    return json.loads(raw)
