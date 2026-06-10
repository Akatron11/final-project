import uuid
import enum
from sqlalchemy import Column, Date, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    suspended = "suspended"
    frozen = "frozen"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gym_id = Column(UUID(as_uuid=True), ForeignKey("gyms.id"), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("membership_plans.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.active)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    member = relationship("Member", back_populates="subscriptions")
    plan = relationship("MembershipPlan", back_populates="subscriptions")
