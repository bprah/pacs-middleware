from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from typing import List

from app.schemas.project import ProjectRead, ProjectCreate, ProjectUpdate
from app.schemas.user import UserSummary
from app.db.crud.crud_project import (
    get_all_projects,
    get_project_by_id,
    create_project,
    update_project,
)
from app.db.crud.crud_user import get_all_users
from app.api.dependencies import get_db, check_roles

router = APIRouter(prefix="/projects", tags=["projects"])


def _serialize_project(p) -> dict:
    """
    Convert a Project ORM instance into a dict matching ProjectRead schema.
    """
    return ProjectRead.model_validate({
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "lead_user_id": p.lead_user_id,
        "member_ids": [u.id for u in p.members],
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }).model_dump()


# ── List all projects ───────────────────────────────────────
@router.get("", response_model=List[ProjectRead])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    _=Depends(check_roles(["admin", "researcher", "viewer"]))
):
    projs = await get_all_projects(db)
    return [_serialize_project(p) for p in projs]


# ── Create new project ──────────────────────────────────────
@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_new_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(check_roles(["admin", "researcher"]))
):
    proj = await create_project(db, payload)
    return _serialize_project(proj)


# ── Update existing project ─────────────────────────────────
@router.put("/{project_id}", response_model=ProjectRead)
async def edit_project(
    project_id: int,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(check_roles(["admin", "researcher"]))
):
    try:
        proj = await update_project(db, project_id, payload)
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
    except IntegrityError as e:
        # Handle unique constraint violation on project name
        if 'ix_projects_name' in str(e.orig):
            raise HTTPException(status_code=400, detail="Project name already exists")
        # propagate other integrity errors
        raise HTTPException(status_code=400, detail="Database integrity error")

    return _serialize_project(proj)

# ── List users for project membership ──────────────────────
@router.get(
    "/users",
    response_model=List[UserSummary],
    dependencies=[Depends(check_roles(["admin", "researcher"]))]
)
async def list_project_users(db: AsyncSession = Depends(get_db)):
    users = await get_all_users(db)
    return [UserSummary.from_orm(u).model_dump() for u in users]
