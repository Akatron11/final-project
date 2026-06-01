from pydantic import BaseModel, EmailStr
from datetime import date


class MemberCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    date_of_birth: date | None = None
    emergency_contact: str | None = None


class MemberUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    emergency_contact: str | None = None
    photo_url: str | None = None


class FlagRequest(BaseModel):
    reason: str
