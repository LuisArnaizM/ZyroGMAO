from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.postgres import get_db
from app.schemas.failure import MaintenanceCreate, MaintenanceRead, MaintenanceUpdate
from app.crud.failure import (
    create_maintenance, 
    get_maintenance, 
    get_all_maintenance,
    update_maintenance, 
    delete_maintenance
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/failures", tags=["Failures"])

@router.post("/", response_model=MaintenanceRead)
async def create_failure(
    failure: MaintenanceCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    return await create_maintenance(db=db, failure=failure)

@router.get("/{failure_id}", response_model=MaintenanceRead)
async def read_failure(
    failure_id: int,
    db: AsyncSession = Depends(get_db)
):
    maintenance = await get_maintenance(db=db, failure_id=failure_id)
    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return maintenance

@router.get("/", response_model=List[MaintenanceRead])
async def read_failures(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    return await get_all_maintenance(db=db, skip=skip, limit=limit)

@router.put("/{failure_id}", response_model=MaintenanceRead)
async def update_failure(
    failure_id: int,
    failure: MaintenanceUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"]))
):
    updated_maintenance = await update_maintenance(db=db, failure_id=failure_id, failure=failure)
    if not updated_maintenance:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return updated_maintenance

@router.delete("/{failure_id}", response_model=dict)
async def delete_failure(
    failure_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    deleted = await delete_maintenance(db=db, failure_id=failure_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return {"detail": "Maintenance request deleted successfully"}