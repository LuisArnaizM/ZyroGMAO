from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.postgres import get_db
from app.schemas.maintenance_plan import (
    MaintenancePlanCreate,
    MaintenancePlanRead,
    MaintenancePlanUpdate,
)
from app.controllers.maintenance_plan import (
    create_maintenance_plan,
    get_maintenance_plan,
    get_all_maintenance_plans,
    update_maintenance_plan,
    delete_maintenance_plan,
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(tags=["MaintenancePlan"])


@router.post("/", response_model=MaintenancePlanRead)
async def create_new_maintenance_plan(
    plan_in: MaintenancePlanCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"]))
):
    return await create_maintenance_plan(db=db, plan_in=plan_in)


@router.get("/{plan_id}", response_model=MaintenancePlanRead)
async def read_maintenance_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    plan = await get_maintenance_plan(db=db, plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="MaintenancePlan not found")
    return plan


@router.get("/", response_model=List[MaintenancePlanRead])
async def read_all_maintenance_plans(
    page: int = Query(1, ge=1, description="Página actual"),
    page_size: int = Query(20, ge=1, le=100, description="Número de elementos por página"),
    search: str = Query(None, description="Término de búsqueda para filtrar planes"),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_maintenance_plans(db=db, page=page, page_size=page_size, search=search)


@router.put("/{plan_id}", response_model=MaintenancePlanRead)
async def update_existing_maintenance_plan(
    plan_id: int,
    plan_in: MaintenancePlanUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"]))
):
    plan = await update_maintenance_plan(db=db, plan_id=plan_id, plan_in=plan_in)
    if not plan:
        raise HTTPException(status_code=404, detail="MaintenancePlan not found")
    return plan


@router.delete("/{plan_id}", response_model=dict)
async def delete_existing_maintenance_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    result = await delete_maintenance_plan(db=db, plan_id=plan_id)
    if not result:
        raise HTTPException(status_code=404, detail="MaintenancePlan not found")
    return {"detail": "MaintenancePlan deleted successfully"}
