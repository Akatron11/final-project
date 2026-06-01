import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Gym(Base):
    __tablename__ = "gyms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    address = Column(String(500), nullable=False)
    phone = Column(String(20))
    email = Column(String(200), unique=True, nullable=False)
    max_capacity = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admins = relationship("Admin", back_populates="gym")
    members = relationship("Member", back_populates="gym")
    plans = relationship("MembershipPlan", back_populates="gym")
    gate_devices = relationship("GateDevice", back_populates="gym")
    access_logs = relationship("AccessLog", back_populates="gym")
