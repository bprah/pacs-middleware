# app/db/crud/crud_pending_registration.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import PendingRegistration, RegistrationStatusEnum
from app.core.security import get_password_hash

async def get_pending_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(PendingRegistration).where(PendingRegistration.email == email))
    return result.scalars().first()

async def create_pending_registration(db: AsyncSession, registration_data: dict) -> PendingRegistration:
    hashed_password = get_password_hash(registration_data["password"])
    pending = PendingRegistration(
        email=registration_data["email"],
        hashed_password=hashed_password,
        first_name=registration_data["first_name"],
        last_name=registration_data["last_name"],
        mobile_phone=registration_data.get("mobile_phone"),
        organisation=registration_data.get("organisation"),
        research_id_doc=registration_data.get("research_id_doc"),
        ethics_approval_doc=registration_data.get("ethics_approval_doc"),
        confidentiality_agreement_doc=registration_data.get("confidentiality_agreement_doc"),
    )
    db.add(pending)
    await db.commit()
    await db.refresh(pending)
    return pending

