from pydantic import BaseModel


class PlanCreate(BaseModel):
    name: str
    description: str | None = None
    duration_days: int
    price: float
    max_freezes: int = 1


class PlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    duration_days: int | None = None
    price: float | None = None
    max_freezes: int | None = None
