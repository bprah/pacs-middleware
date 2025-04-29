# app/db/crud/crud_user.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import User
from app.core.security import get_password_hash
from typing import List
from app.db.models import Role

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    mobile_phone: str | None,
    organisation: str | None,
    research_id_doc: str | None,
    ethics_approval_doc: str | None,
    confidentiality_agreement_doc: str | None,
    role_objs: List[Role],
    hashed: bool = False
) -> User:
    pwd = password if hashed else get_password_hash(password)
    user = User(
        email=email,
        hashed_password=pwd,
        first_name=first_name,
        last_name=last_name,
        mobile_phone=mobile_phone,
        organisation=organisation,
        research_id_doc=research_id_doc,
        ethics_approval_doc=ethics_approval_doc,
        confidentiality_agreement_doc=confidentiality_agreement_doc,
        roles=role_objs,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def get_all_users(db: AsyncSession) -> List[User]:
    """
    Return all active users, for things like project member pickers.
    """
    result = await db.execute(
        select(User).where(User.is_active == True)
    )
    return result.scalars().all()