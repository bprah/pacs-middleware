# app/db/crud/crud_role.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db.models import Role

async def get_role_by_name(db: AsyncSession, name: str) -> Role | None:
    result = await db.execute(select(Role).where(Role.name == name))
    return result.scalars().first()

async def create_role(db: AsyncSession, name: str, description: str | None = None) -> Role:
    role = Role(name=name)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role

async def get_roles_by_ids(db: AsyncSession, role_ids: List[int]) -> List[Role]:
    result = await db.execute(select(Role).where(Role.id.in_(role_ids)))
    roles = result.scalars().all()
    if len(roles) != len(role_ids):
        raise ValueError("One or more role IDs are invalid")
    return roles
