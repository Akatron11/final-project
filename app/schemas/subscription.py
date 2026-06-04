from pydantic import BaseModel
from datetime import date
from uuid import UUID


class SubscriptionCreate(BaseModel):
    plan_id: UUID
    start_date: date
