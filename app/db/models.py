# app/db/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class RegistrationStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    mobile_phone = Column(String, nullable=True)
    organisation = Column(String, nullable=True)

    research_id_doc = Column(String, nullable=True)
    ethics_approval_doc = Column(String, nullable=True)
    confidentiality_agreement_doc = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 🔐 TOTP support
    totp_secret = Column(String, nullable=True)
    is_totp_verified = Column(Boolean, default=False)

    # 🚫 Login protection
    failed_login_attempts = Column(Integer, default=0)
    lock_until = Column(DateTime(timezone=True), nullable=True)

    roles = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin"
    )

class PendingRegistration(Base):
    __tablename__ = "pending_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    mobile_phone = Column(String, nullable=True)
    organisation = Column(String, nullable=True)
    research_id_doc = Column(String, nullable=True)  # file path to Research ID PDF
    ethics_approval_doc = Column(String, nullable=True)  # file path to Ethics Approval PDF
    confidentiality_agreement_doc = Column(String, nullable=True)  # file path to Confidentiality Agreement PDF
    status = Column(Enum(RegistrationStatusEnum), default=RegistrationStatusEnum.pending, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

