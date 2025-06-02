from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.postgres import get_db
from app.schemas.maintenance import MaintenanceCreate, MaintenanceRead, MaintenanceUpdate
from app.controllers.maintenance import (
    create_maintenance, 
    get_maintenance, 
    get_all_maintenance,
    get_maintenance_by_asset,
    update_maintenance, 
    delete_maintenance
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])

@router.post("/", response_model=MaintenanceRead)
async def create_new_maintenance(
    maintenance_in: MaintenanceCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"]))
):
    return await create_maintenance(db=db, maintenance_in=maintenance_in)

@router.get("/{maintenance_id}", response_model=MaintenanceRead)
async def read_maintenance(
    maintenance_id: int,
    db: AsyncSession = Depends(get_db)
):
    maintenance = await get_maintenance(db=db, maintenance_id=maintenance_id)
    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return maintenance

@router.get("/", response_model=List[MaintenanceRead])
async def read_all_maintenance(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    return await get_all_maintenance(db=db, skip=skip, limit=limit)

@router.get("/asset/{asset_id}", response_model=List[MaintenanceRead])
async def read_maintenance_by_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_maintenance_by_asset(db=db, asset_id=asset_id)

@router.put("/{maintenance_id}", response_model=MaintenanceRead)
async def update_existing_maintenance(
    maintenance_id: int,
    maintenance_in: MaintenanceUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"]))
):
    maintenance = await update_maintenance(db=db, maintenance_id=maintenance_id, maintenance_in=maintenance_in)
    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return maintenance

@router.delete("/{maintenance_id}", response_model=dict)
async def delete_existing_maintenance(
    maintenance_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    result = await delete_maintenance(db=db, maintenance_id=maintenance_id)
    if not result:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return {"detail": "Maintenance deleted successfully"}