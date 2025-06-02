from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.postgres import get_db
from app.schemas.workorder import WorkOrderCreate, WorkOrderRead, WorkOrderUpdate
from app.controllers.workorder import (
    create_workorder, 
    get_workorder, 
    get_workorders,
    get_workorders_by_maintenance,
    update_workorder, 
    delete_workorder
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/workorders", tags=["WorkOrders"])

@router.post("/", response_model=WorkOrderRead)
async def create_new_workorder(
    workorder_in: WorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"]))
):
    return await create_workorder(
        db=db, 
        workorder_in=workorder_in, 
        created_by=user["email"]
    )

@router.get("/{workorder_id}", response_model=WorkOrderRead)
async def read_workorder(
    workorder_id: int,
    db: AsyncSession = Depends(get_db)
):
    workorder = await get_workorder(db=db, workorder_id=workorder_id)
    if not workorder:
        raise HTTPException(status_code=404, detail="WorkOrder not found")
    return workorder

@router.get("/", response_model=List[WorkOrderRead])
async def read_workorders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    return await get_workorders(db=db, skip=skip, limit=limit)

@router.get("/maintenance/{maintenance_id}", response_model=List[WorkOrderRead])
async def read_workorders_by_maintenance(
    maintenance_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_workorders_by_maintenance(db=db, maintenance_id=maintenance_id)

@router.put("/{workorder_id}", response_model=WorkOrderRead)
async def update_existing_workorder(
    workorder_id: int,
    workorder_in: WorkOrderUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"]))
):
    workorder = await update_workorder(db=db, workorder_id=workorder_id, workorder_in=workorder_in)
    if not workorder:
        raise HTTPException(status_code=404, detail="WorkOrder not found")
    return workorder

@router.delete("/{workorder_id}", response_model=dict)
async def delete_existing_workorder(
    workorder_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    result = await delete_workorder(db=db, workorder_id=workorder_id)
    if not result:
        raise HTTPException(status_code=404, detail="WorkOrder not found")
    return {"detail": "WorkOrder deleted successfully"}