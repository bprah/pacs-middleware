# app/db/models.py
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
import enum
from app.db.database import Base

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

class PendingRegistration(Base):
    __tablename__ = "pending_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    status = Column(Enum(RegistrationStatusEnum), default=RegistrationStatusEnum.pending, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

