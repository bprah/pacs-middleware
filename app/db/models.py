# app/db/models.py
from sqlalchemy import Table, Column, Integer, ForeignKey, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

# Define the association table for the many-to-many relationship between User and Role.
user_roles = Table(
    'user_roles',  # name of the association table in the database.
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)
project_members = Table(
    "project_members",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("user_id",    Integer, ForeignKey("users.id"),    primary_key=True),
)

class RegistrationStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class EthnicityEnum(str, enum.Enum):
    asian      = "asian"
    black      = "black"
    white      = "white"
    hispanic   = "hispanic"
    indigenous = "indigenous"
    other      = "other"
    unknown    = "unknown"

class GenderEnum(str, enum.Enum):
    male    = "male"
    female  = "female"
    other   = "other"
    unknown = "unknown"

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
    totp_secret = Column(String, nullable=True)
    is_totp_verified = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    lock_until = Column(DateTime(timezone=True), nullable=True)
    # patients = relationship("Patients",back_populates="added_by_user")

    roles = relationship(
        "Role",
        secondary=user_roles,  # Reference the association table (or its name as a string)
        back_populates="users",
        lazy="selectin"
    )
    patients = relationship(
        "Patient",
        back_populates="added_by_user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )

    led_projects = relationship(
        "Project",
        back_populates="lead_user",
        lazy="selectin",
    )

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
    users = relationship(
        "User",
        secondary=user_roles,  # Same join table referenced here.
        back_populates="roles",
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
    research_id_doc = Column(String, nullable=True)
    ethics_approval_doc = Column(String, nullable=True)
    confidentiality_agreement_doc = Column(String, nullable=True)
    status = Column(Enum(RegistrationStatusEnum), default=RegistrationStatusEnum.pending, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

class Patient(Base):
    __tablename__ = "patients"

    # Auto PK
    id                     = Column(Integer, primary_key=True, index=True)

    # Mandatory
    first_name             = Column(String, nullable=False)
    last_name              = Column(String, nullable=False)
    dob                    = Column(String, nullable=False)
    ethnicity              = Column(Enum(EthnicityEnum, name="ethnicity_enum"), nullable=False)
    gender                 = Column(Enum(GenderEnum,    name="gender_enum"),    nullable=False)

    # Optional clinical data
    past_diagnoses         = Column(String,  nullable=True)
    informed_consent_doc   = Column(String,  nullable=True)
    related_reports_doc    = Column(String,  nullable=True)
    family_medical_history = Column(String,  nullable=True)
    current_prescriptions  = Column(String,  nullable=True)
    smoking_status         = Column(Boolean, nullable=True)
    alcohol_status         = Column(Boolean, nullable=True)
    drug_use               = Column(Boolean, nullable=True)

    # Audit
    added_at               = Column(DateTime(timezone=True), server_default=func.now())
    added_by_user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    added_by_user          = relationship("User", back_populates="patients")

class Project(Base):
    __tablename__ = "projects"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    lead_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lead_user    = relationship(
        "User",
        back_populates="led_projects",
        lazy="selectin",
    )

    members = relationship(
        "User",
        secondary=project_members,
        lazy="selectin",
    )

    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())