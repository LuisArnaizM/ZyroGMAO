from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database.postgres import get_db
from app.schemas.workorder import WorkOrderCreate, WorkOrderRead, WorkOrderUpdate, WorkOrderCompleteRequest, WorkOrderCompleteResult
from app.controllers.workorder import (
    create_workorder,
    get_workorder,
    get_workorders,
    get_workorders_by_asset,
    get_workorders_by_user,
    update_workorder,
    delete_workorder
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(tags=["Work Orders"])

@router.post("/", response_model=WorkOrderRead)
async def create_new_workorder(
    workorder_in: WorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    return await create_workorder(
        db=db,
        workorder_in=workorder_in,
        created_by=user["id"],
    )

@router.get("/{workorder_id}", response_model=WorkOrderRead)
async def read_workorder(
    workorder_id: int,
    db: AsyncSession = Depends(get_db)
):
    workorder = await get_workorder(db=db, workorder_id=workorder_id)
    if not workorder:
        raise HTTPException(status_code=404, detail="Work order not found")
    return workorder

@router.get("/", response_model=List[WorkOrderRead])
async def read_workorders(
    page: int = Query(1, ge=1, description="Página actual"),
    page_size: int = Query(20, ge=1, le=1000, description="Número de elementos por página"),
    search: str = Query(None, description="Término de búsqueda para filtrar órdenes de trabajo"),
    status: str = Query(None, description="Filtrar por estado"),
    work_type: str = Query(None, description="Filtrar por tipo de trabajo"),
    priority: str = Query(None, description="Filtrar por prioridad"),
    assigned_to: int = Query(None, description="Filtrar por usuario asignado"),
    db: AsyncSession = Depends(get_db)
):
    return await get_workorders(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        work_type=work_type,
        priority=priority,
        assigned_to=assigned_to
    )

@router.get("/asset/{asset_id}", response_model=List[WorkOrderRead])
async def read_workorders_by_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_workorders_by_asset(db=db, asset_id=asset_id)

@router.get("/user/{user_id}", response_model=List[WorkOrderRead])
async def read_workorders_by_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_workorders_by_user(db=db, user_id=user_id)

@router.put("/{workorder_id}", response_model=WorkOrderRead)
async def update_existing_workorder(
    workorder_id: int,
    workorder_in: WorkOrderUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"]))
):
    # Convert WorkOrderUpdate to dict, excluding None values
    update_data = {k: v for k, v in workorder_in.dict(exclude_unset=True).items() if v is not None}
    
    workorder = await update_workorder(
        db=db,
        workorder_id=workorder_id,
        update_data=update_data,
    )
    if not workorder:
        raise HTTPException(status_code=404, detail="Work order not found")
    return workorder

@router.post("/{workorder_id}/complete", response_model=WorkOrderCompleteResult)
async def complete_workorder(
    workorder_id: int,
    complete_data: WorkOrderCompleteRequest | None = None,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    """Completa una workorder (status -> COMPLETED) y dispara creación automática de maintenance."""
    try:
        created_container = {}
        workorder = await update_workorder(
            db=db,
            workorder_id=workorder_id,
            update_data={"status": "COMPLETED"},
            maintenance_notes=complete_data.maintenance_notes if complete_data else None,
            _created_maintenance=created_container,
        )
        if not workorder:
            raise HTTPException(status_code=404, detail="Work order not found")
        return {"workorder": workorder, "maintenance": created_container.get('maintenance')}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{workorder_id}", response_model=dict)
async def delete_existing_workorder(
    workorder_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    result = await delete_workorder(db=db, workorder_id=workorder_id)
    if not result:
        raise HTTPException(status_code=404, detail="Work order not found")
    return {"detail": "Work order deleted successfully"}