# app/db/crud/crud_pending_registration.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import PendingRegistration, RegistrationStatusEnum
from app.core.security import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from typing import List


from app.db.crud.crud_user import create_user
from app.db.crud.crud_role import get_roles_by_ids

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



async def get_all_pending(db: AsyncSession) -> List[PendingRegistration]:
    result = await db.execute(
        select(PendingRegistration).where(PendingRegistration.status == RegistrationStatusEnum.pending)
    )
    return result.scalars().all()

async def get_pending_by_id(db: AsyncSession, pending_id: int) -> PendingRegistration | None:
    result = await db.execute(
        select(PendingRegistration).where(PendingRegistration.id == pending_id)
    )
    return result.scalars().first()

async def approve_pending_registration(
    db: AsyncSession,
    pending: PendingRegistration,
    role_ids: List[int]
):
    # Fetch role objects
    role_objs = await get_roles_by_ids(db, role_ids)
    # Create the user
    new_user = await create_user(
        db,
        email=pending.email,
        password=pending.hashed_password,  # already hashed
        first_name=pending.first_name,
        last_name=pending.last_name,
        mobile_phone=pending.mobile_phone,
        organisation=pending.organisation,
        research_id_doc=pending.research_id_doc,
        ethics_approval_doc=pending.ethics_approval_doc,
        confidentiality_agreement_doc=pending.confidentiality_agreement_doc,
        role_objs=role_objs,
        hashed=True
    )
    # Delete the pending registration
    await delete_pending_by_id(db, pending.id)
    return new_user

async def delete_pending_by_id(db: AsyncSession, pending_id: int):
    pending = await get_pending_by_id(db, pending_id)
    if pending:
        await db.delete(pending)
        await db.commit()
