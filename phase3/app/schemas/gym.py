from pydantic import BaseModel


class GymUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    max_capacity: int | None = None
