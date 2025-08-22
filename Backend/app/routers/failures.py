from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database.postgres import get_db
from app.schemas.failure import FailureCreate, FailureRead, FailureUpdate
from app.controllers.failure import (
    create_failure,
    get_failure,
    get_failures,
    get_failures_by_asset,
    update_failure,
    delete_failure
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(tags=["Failures"])

@router.post("/", response_model=FailureRead)
async def create_new_failure(
    failure_in: FailureCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"]))
):
    return await create_failure(db=db, failure_in=failure_in, reported_by=user["id"])

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
async def read_failures(
    page: int = Query(1, ge=1, description="Página actual"),
    page_size: int = Query(20, ge=1, le=100, description="Número de elementos por página"),
    search: str = Query(None, description="Término de búsqueda para filtrar fallos"),
    status: str = Query(None, description="Filtrar por estado"),
    severity: str = Query(None, description="Filtrar por severidad"),
    db: AsyncSession = Depends(get_db)
):
    return await get_failures(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        severity=severity
    )

@router.get("/asset/{asset_id}", response_model=List[FailureRead])
async def read_failures_by_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_failures_by_asset(db=db, asset_id=asset_id)

@router.put("/{failure_id}", response_model=FailureRead)
async def update_existing_failure(
    failure_id: int,
    failure_in: FailureUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"]))
):
    failure = await update_failure(
        db=db,
        failure_id=failure_id,
        failure_in=failure_in,
    )
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