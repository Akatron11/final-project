import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AccessDecision(str, enum.Enum):
    GRANTED = "GRANTED"
    DENIED_EXPIRED = "DENIED_EXPIRED"
    DENIED_SUSPENDED = "DENIED_SUSPENDED"
    DENIED_FROZEN = "DENIED_FROZEN"
    DENIED_UNKNOWN = "DENIED_UNKNOWN"
    DENIED_FLAGGED = "DENIED_FLAGGED"
    DENIED_ALREADY_INSIDE = "DENIED_ALREADY_INSIDE"
    DENIED_NOT_INSIDE = "DENIED_NOT_INSIDE"


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gym_id = Column(UUID(as_uuid=True), ForeignKey("gyms.id"), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id"), nullable=True)
    gate_id = Column(String(200), nullable=False)
    credential_type = Column(String(10), nullable=False)
    action = Column(String(10), default="entry")
    decision = Column(Enum(AccessDecision), nullable=False)
    is_flag_log = Column(Boolean, default=False)
    scanned_at = Column(DateTime(timezone=True), server_default=func.now())

    gym = relationship("Gym", back_populates="access_logs")
    member = relationship("Member", back_populates="access_logs")
