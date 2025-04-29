# app/db/crud/crud_project.py
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Project, User
from app.schemas.project import ProjectCreate, ProjectUpdate

async def get_all_projects(db: AsyncSession) -> List[Project]:
    result = await db.execute(select(Project))
    return result.scalars().all()

async def get_project_by_id(db: AsyncSession, project_id: int) -> Optional[Project]:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalars().first()

async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
    # enforce max 12 members
    if len(data.member_ids) > 12:
        raise HTTPException(status_code=400, detail="Cannot assign more than 12 members")

    # fetch and validate lead
    lead = await db.get(User, data.lead_user_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead user not found")

    proj = Project(
        name=data.name,
        description=data.description,
        lead_user=lead
    )

    # fetch and validate members
    members = []
    for uid in data.member_ids:
        u = await db.get(User, uid)
        if not u:
            raise HTTPException(status_code=404, detail=f"Member user {uid} not found")
        members.append(u)
    proj.members = members

    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj

async def update_project(
    db: AsyncSession,
    project_id: int,
    data: ProjectUpdate
) -> Optional[Project]:
    proj = await get_project_by_id(db, project_id)
    if not proj:
        return None

    upd = data.model_dump(exclude_unset=True)

    # handle member_ids specially
    if "member_ids" in upd:
        mids = upd.pop("member_ids") or []
        if len(mids) > 12:
            raise HTTPException(status_code=400, detail="Cannot assign more than 12 members")
        members = []
        for uid in mids:
            u = await db.get(User, uid)
            if not u:
                raise HTTPException(status_code=404, detail=f"Member user {uid} not found")
            members.append(u)
        proj.members = members

    # apply other fields
    for field, value in upd.items():
        setattr(proj, field, value)

    await db.commit()
    await db.refresh(proj)
    return proj
