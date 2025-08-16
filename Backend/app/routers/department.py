from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.controllers.department import (
    create_department,
    get_department,
    update_department,
    delete_department,
    list_departments,
    list_users_in_department_subtree,
)
from app.schemas.user import UserRead
from app.auth.dependencies import require_role, get_current_organization


router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("/", response_model=DepartmentRead)
async def create_dep(
    dep_in: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    dep = await create_department(db, dep_in)
    return dep


@router.get("/", response_model=List[DepartmentRead])
async def list_deps(
    db: AsyncSession = Depends(get_db),
    org = Depends(get_current_organization)
):
    return await list_departments(db, organization_id=org.id)


@router.get("/{dep_id}", response_model=DepartmentRead)
async def get_dep(
    dep_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    dep = await get_department(db, dep_id)
    if not dep:
        raise HTTPException(status_code=404, detail="Department not found")
    return dep


@router.put("/{dep_id}", response_model=DepartmentRead)
async def update_dep(
    dep_id: int,
    dep_in: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    dep = await update_department(db, dep_id, dep_in)
    if not dep:
        raise HTTPException(status_code=404, detail="Department not found")
    return dep


@router.delete("/{dep_id}")
async def delete_dep(
    dep_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin"]))
):
    ok = await delete_department(db, dep_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Department not found")
    return {"detail": "Department deleted"}


@router.get("/{dep_id}/users", response_model=List[UserRead])
async def users_in_subtree(
    dep_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    return await list_users_in_department_subtree(db, dep_id)
