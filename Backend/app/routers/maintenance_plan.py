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
from sqlalchemy.future import select
from sqlalchemy import exists
from datetime import datetime, timedelta, timezone
from app.config import settings
from app.models.maintenancePlan import MaintenancePlan
from app.models.workorder import WorkOrder
from app.models.enums import WorkOrderStatus
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(tags=["MaintenancePlan"])


ACTIVE_WO_STATUSES = {
    WorkOrderStatus.OPEN.value,
    WorkOrderStatus.ASSIGNED.value,
    WorkOrderStatus.IN_PROGRESS.value,
}

@router.get("/upcoming", response_model=List[MaintenancePlanRead])
async def read_upcoming_maintenance_plans(
    window_days: int = Query(None, ge=1, le=365, description="Días hacia adelante a considerar"),
    asset_id: int = Query(None, description="Filtrar por asset"),
    show_blocked: bool = Query(False, description="Si true incluye planes con WO activa pendiente"),
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"]))
):
    """Listado de planes próximos (next_due_date en rango) que no tienen una WorkOrder activa asociada.
    Un plan se considera *bloqueado* si existe una WorkOrder con status OPEN / ASSIGNED / IN_PROGRESS y plan_id = plan.id.
    Hasta que esa WorkOrder no se complete/cancele, el plan no vuelve a aparecer (persistencia en backend).
    Param show_blocked permite incluirlos (debug / auditoría).
    """
    days = window_days or settings.UPCOMING_PLANS_WINDOW_DAYS
    now = datetime.now(timezone.utc)
    upper = now + timedelta(days=days)
    now_naive = now.astimezone(timezone.utc).replace(tzinfo=None)
    upper_naive = upper.astimezone(timezone.utc).replace(tzinfo=None)

    # EXISTS correlacionado: hay al menos una WO activa ligada al plan
    active_wo_exists = exists().where(
        WorkOrder.plan_id == MaintenancePlan.id,
        WorkOrder.status.in_(ACTIVE_WO_STATUSES)
    )

    query = select(MaintenancePlan).where(
        MaintenancePlan.next_due_date.isnot(None),
        MaintenancePlan.next_due_date >= now_naive,
        MaintenancePlan.next_due_date <= upper_naive,
    )
    if asset_id is not None:
        query = query.where(MaintenancePlan.asset_id == asset_id)
    if not show_blocked:
        # Excluir planes con WO activa
        query = query.where(~active_wo_exists)

    result = await db.execute(query)
    return result.scalars().all()

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
    asset_id: int = Query(None, description="Filter by asset id"),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_maintenance_plans(db=db, page=page, page_size=page_size, search=search, asset_id=asset_id)

# Versión sin slash final para evitar 422 cuando se llama /maintenance/plans sin "/"
@router.get("", response_model=List[MaintenancePlanRead], include_in_schema=False)
async def read_all_maintenance_plans_noslash(
    page: int = Query(1, ge=1, description="Página actual"),
    page_size: int = Query(20, ge=1, le=100, description="Número de elementos por página"),
    search: str = Query(None, description="Término de búsqueda para filtrar planes"),
    asset_id: int = Query(None, description="Filter by asset id"),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_maintenance_plans(db=db, page=page, page_size=page_size, search=search, asset_id=asset_id)


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


## Eliminada duplicación de ruta /upcoming previa (con conflicto)
