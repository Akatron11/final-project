import uuid
from sqlalchemy import Column, String, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Member(Base):
    __tablename__ = "members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gym_id = Column(UUID(as_uuid=True), ForeignKey("gyms.id"), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(20))
    date_of_birth = Column(Date)
    emergency_contact = Column(String(20))
    photo_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    gym = relationship("Gym", back_populates="members")
    subscriptions = relationship("Subscription", back_populates="member")
    credentials = relationship("Credential", back_populates="member")
    access_logs = relationship("AccessLog", back_populates="member")
