# app/api/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.registration import PendingRegistrationRead, RegistrationApprove
from app.schemas.user import UserRead
from app.db.crud.crud_pending_registration import (
    get_all_pending,
    get_pending_by_id,
    approve_pending_registration,
    delete_pending_by_id
)
from app.api.dependencies import get_db, check_roles

router = APIRouter()

@router.get(
    "/pending-registrations",
    response_model=List[PendingRegistrationRead]
)
async def list_pending(
    db: AsyncSession = Depends(get_db),
    _=Depends(check_roles(["admin"]))
):
    pendings = await get_all_pending(db)
    return [PendingRegistrationRead.from_orm(p).model_dump() for p in pendings]


@router.post(
    "/pending-registrations/{pending_id}/approve",
    response_model=UserRead
)
async def approve(
    data: RegistrationApprove = Body(...),
    pending_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    _=Depends(check_roles(["admin"]))
):
    pending = await get_pending_by_id(db, pending_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Pending registration not found")

    new_user = await approve_pending_registration(db, pending, data.role_ids)

    # Manually serialize new_user into the UserRead schema
    user_dict = {
        "id": new_user.id,
        "email": new_user.email,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
        "mobile_phone": new_user.mobile_phone,
        "organisation": new_user.organisation,
        "roles": [role.name for role in new_user.roles],
        "created_at": new_user.created_at,
        "updated_at": new_user.updated_at,
    }
    return UserRead.model_validate(user_dict).model_dump()


@router.delete(
    "/pending-registrations/{pending_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def reject(
    pending_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    _=Depends(check_roles(["admin"]))
):
    pending = await get_pending_by_id(db, pending_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Pending registration not found")
    await delete_pending_by_id(db, pending_id)
    return None
