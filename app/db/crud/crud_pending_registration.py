# app/db/crud/crud_pending_registration.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import PendingRegistration, RegistrationStatusEnum
from app.core.security import get_password_hash

async def get_pending_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(PendingRegistration).where(PendingRegistration.email == email))
    return result.scalars().first()

async def create_pending_registration(db: AsyncSession, registration_req) -> PendingRegistration:
    hashed_password = get_password_hash(registration_req.password)
    pending = PendingRegistration(
        email=registration_req.email,
        hashed_password=hashed_password,
        first_name=registration_req.first_name,
        last_name=registration_req.last_name,
    )
    db.add(pending)
    await db.commit()
    await db.refresh(pending)
    return pending

