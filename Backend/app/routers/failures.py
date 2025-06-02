from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.postgres import get_db
from app.schemas.failure import FailureCreate, FailureRead, FailureUpdate
from app.controllers.failure import (
    create_failure,
    get_failure,
    get_failures,
    update_failure,
    delete_failure
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(
    prefix="/failures",
    tags=["Failures"]
)

@router.post("/", response_model=FailureRead)
async def create_new_failure(
    failure_in: FailureCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    return await create_failure(db=db, failure=failure_in)

@router.get("/{failure_id}", response_model=FailureRead)
async def read_failure(
    failure_id: int,
    db: AsyncSession = Depends(get_db)
):
    failure = await get_failure(db=db, failure_id=failure_id)
    if not failure:
        raise HTTPException(status_code=404, detail="Failure not found")
    return failure

@router.get("/", response_model=List[FailureRead])
async def read_all_failures(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    return await get_failures(db=db, skip=skip, limit=limit)

@router.put("/{failure_id}", response_model=FailureRead)
async def update_existing_failure(
    failure_id: int,
    failure_in: FailureUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"]))
):
    failure = await update_failure(db=db, failure_id=failure_id, failure=failure_in)
    if not failure:
        raise HTTPException(status_code=404, detail="Failure not found")
    return failure

@router.delete("/{failure_id}", response_model=dict)
async def delete_existing_failure(
    failure_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    result = await delete_failure(db=db, failure_id=failure_id)
    if not result:
        raise HTTPException(status_code=404, detail="Failure not found")
    return {"detail": "Failure deleted successfully"}