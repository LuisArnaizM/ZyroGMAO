from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database.postgres import get_db
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserProfile
from app.controllers.user import (
    create_user, 
    get_user, 
    get_users, 
    update_user, 
    update_password,
    delete_user,
    get_department_managers
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(tags=["Users"])

@router.post("/", response_model=UserRead)
async def create_new_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin"]))
):
    new_user = await create_user(db=db, user_in=user_in)
    if not new_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return new_user

@router.get("/me", response_model=UserProfile)
async def read_users_me(
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)    
):
    db_user = await get_user(db=db, user_id = user["id"])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile.from_user(db_user)


@router.get("/managers", response_model=List[UserRead])
async def get_managers(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    """Devuelve los usuarios que son managers de algún departamento."""
    return await get_department_managers(db=db)

@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    db_user = await get_user(db=db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/", response_model=List[UserRead])
async def read_users(
    page: int = Query(1, ge=1, description="Página actual"),
    page_size: int = Query(20, ge=1, le=100, description="Número de elementos por página"),
    search: Optional[str] = Query(None, description="Término de búsqueda"),
    role: Optional[str] = Query(None, description="Filtrar por rol exacto"),
    is_active: Optional[bool] = Query(None, description="true activo, false inactivo"),
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    return await get_users(db=db, page=page, page_size=page_size, search=search, role=role, is_active=is_active)

@router.put("/{user_id}", response_model=UserRead)
async def update_existing_user(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin"]))
):
    updated_user = await update_user(db=db, user_id=user_id, user_in=user_in)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.put("/{user_id}/password")
async def change_user_password(
    user_id: int,
    password: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin"]))
):
    updated_user = await update_password(db=db, user_id=user_id, new_password=password)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "Password updated successfully"}

@router.delete("/{user_id}", response_model=dict)
async def delete_existing_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin"]))
):
    result = await delete_user(db=db, user_id=user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted successfully"}