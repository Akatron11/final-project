from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    gym_name: str
    gym_address: str
    gym_phone: str
    gym_email: EmailStr
    gym_max_capacity: int = 100
    admin_email: EmailStr
    admin_password: str
    admin_full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    gym_id: str
