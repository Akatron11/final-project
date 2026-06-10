import uuid
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class MembershipPlan(Base):
    __tablename__ = "membership_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gym_id = Column(UUID(as_uuid=True), ForeignKey("gyms.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    duration_days = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    gym = relationship("Gym", back_populates="plans")
    subscriptions = relationship("Subscription", back_populates="plan")
