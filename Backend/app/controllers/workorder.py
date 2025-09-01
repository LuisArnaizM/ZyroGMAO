from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi import HTTPException
from app.models.workorder import WorkOrder
from app.models.asset import Asset
from app.models.failure import Failure
from app.models.enums import WorkOrderStatus
from app.schemas.workorder import WorkOrderCreate, WorkOrderRead, WorkOrderUpdate
from datetime import datetime, timezone
from app.models.user import User
from app.models.department import Department

async def create_workorder(db: AsyncSession, workorder_in: WorkOrderCreate, created_by: int):
    """Create a new work order"""
    
    # Verificar que el asset existe en la organización
    asset = await db.execute(select(Asset).where(Asset.id == workorder_in.asset_id))
    if not asset.scalar_one_or_none():
        raise ValueError(f"Asset with ID {workorder_in.asset_id} does not exist in this organization")
    
    # Verificar failure si se proporciona
    if workorder_in.failure_id:
        failure = await db.execute(select(Failure).where(Failure.id == workorder_in.failure_id))
        if not failure.scalar_one_or_none():
            raise ValueError(f"Failure with ID {workorder_in.failure_id} does not exist in this organization")
        
        # Verificar que no existe ya un workorder para esta failure
        existing_workorder = await db.execute(
            select(WorkOrder).where(WorkOrder.failure_id == workorder_in.failure_id)
        )
        if existing_workorder.scalar_one_or_none():
            raise ValueError(f"A work order already exists for failure ID {workorder_in.failure_id}")
    
    def to_naive_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        # Convert aware -> naive UTC
        if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    workorder_data = workorder_in.model_dump()
    # Normalize datetime fields to naive UTC for columns without timezone
    if workorder_data.get('scheduled_date'):
        workorder_data['scheduled_date'] = to_naive_utc(workorder_data['scheduled_date'])
    workorder_data['created_by'] = created_by
    # organization removed
    
    new_workorder = WorkOrder(**workorder_data)
    db.add(new_workorder)
    await db.commit()
    await db.refresh(new_workorder)
    return new_workorder

async def get_workorder(db: AsyncSession, workorder_id: int):
    """Get a work order by ID within organization"""
    result = await db.execute(
    select(WorkOrder).where(WorkOrder.id == workorder_id)
    )
    return result.scalar_one_or_none()

async def get_workorders(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    status: str = None,
    work_type: str = None,
    priority: str = None,
    assigned_to: int = None
):
    """Get all work orders with filters, pagination and search capability"""
    offset = (page - 1) * page_size
    
    query = select(WorkOrder)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (WorkOrder.title.ilike(search_term)) |
            (WorkOrder.description.ilike(search_term))
        )
    
    if status:
        query = query.where(WorkOrder.status == status)
    
    if work_type:
        query = query.where(WorkOrder.work_type == work_type)
    
    if priority:
        query = query.where(WorkOrder.priority == priority)
    
    if assigned_to:
        query = query.where(WorkOrder.assigned_to == assigned_to)
    
    query = query.offset(offset).limit(page_size).order_by(WorkOrder.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def get_workorders_by_asset(db: AsyncSession, asset_id: int):
    """Get all work orders for a specific asset"""
    result = await db.execute(
        select(WorkOrder).where(WorkOrder.asset_id == asset_id).order_by(WorkOrder.created_at.desc())
    )
    return result.scalars().all()

async def get_workorders_by_user(db: AsyncSession, user_id: int):
    """Get all work orders assigned to a specific user"""
    result = await db.execute(
        select(WorkOrder).where(WorkOrder.assigned_to == user_id).order_by(WorkOrder.scheduled_date.asc())
    )
    return result.scalars().all()

async def update_workorder(db: AsyncSession, workorder_id: int, update_data: dict, maintenance_notes: str | None = None, _created_maintenance: dict | None = None) -> WorkOrder:
    """Actualiza una orden de trabajo y crea automáticamente un maintenance al completarse.
    - Calcula horas y coste reales al pasar a COMPLETED.
    - Si el estado cambia a COMPLETED (y antes no lo estaba) crea registro Maintenance (si no existe) usando datos de la WO.
    - Puede añadir notas al maintenance (maintenance_notes).
    """
    workorder = await get_workorder(db, workorder_id)
    if not workorder:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")

    old_status = workorder.status

    # Si el estado cambia a COMPLETED, calcular automáticamente los valores reales
    if update_data.get("status") == WorkOrderStatus.COMPLETED.value and old_status != WorkOrderStatus.COMPLETED.value:
        print(f"DEBUG: Calculando valores automáticos para workorder {workorder_id}")

        from sqlalchemy.orm import joinedload
        from sqlalchemy import select
        from app.models.task import Task
        from app.models.inventory import TaskUsedComponent, InventoryItem

        tasks_query = select(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.used_components).joinedload(TaskUsedComponent.component)
        ).where(Task.workorder_id == workorder_id)

        result = await db.execute(tasks_query)
        tasks = result.scalars().unique().all()

        total_hours = 0.0
        total_cost = 0.0

        for task in tasks:
            if task.actual_hours:
                total_hours += task.actual_hours
                if task.assignee and task.assignee.hourly_rate:
                    labor_cost = task.actual_hours * task.assignee.hourly_rate
                else:
                    labor_cost = task.actual_hours * 50.0  # default rate
                total_cost += labor_cost
                print(f"DEBUG: Task {task.id} labor cost agregado = {labor_cost}")

            for used_component in task.used_components:
                if used_component.unit_cost_snapshot and used_component.quantity:
                    component_cost = used_component.unit_cost_snapshot * used_component.quantity
                elif used_component.component and used_component.component.inventory_item and used_component.quantity and used_component.component.inventory_item.unit_cost:
                    component_cost = used_component.component.inventory_item.unit_cost * used_component.quantity
                else:
                    component_cost = 0
                total_cost += component_cost
                if component_cost:
                    print(f"DEBUG: Task {task.id} component cost agregado = {component_cost}")

        update_data["actual_hours"] = total_hours
        update_data["actual_cost"] = total_cost
        update_data["completed_date"] = datetime.now(timezone.utc).replace(tzinfo=None)
        print(f"DEBUG: Totales calculados - Horas: {total_hours}, Costo: {total_cost}")

    # Aplicar updates
    for key, value in update_data.items():
        setattr(workorder, key, value)

    try:
        await db.commit()
        await db.refresh(workorder)
    except Exception as e:
        await db.rollback()
        print(f"ERROR: Fallo al actualizar workorder: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar la orden de trabajo: {str(e)}")

    # Auto-create maintenance si recién se completó
    if workorder.status == WorkOrderStatus.COMPLETED.value and old_status != WorkOrderStatus.COMPLETED.value:
        try:
            from sqlalchemy import select as _select
            from app.models.maintenance import Maintenance as _MaintenanceModel
            existing = await db.execute(
                _select(_MaintenanceModel.id).where(_MaintenanceModel.workorder_id == workorder.id).limit(1)
            )
            if existing.scalar() is None:
                print(f"DEBUG: Creando maintenance para WO {workorder.id}")
                from app.controllers.maintenance import create_maintenance
                from app.schemas.maintenance import MaintenanceCreate
                from app.models.enums import MaintenanceType

                mtype_map = {
                    'MAINTENANCE': MaintenanceType.PREVENTIVE,
                    'REPAIR': MaintenanceType.CORRECTIVE,
                    'INSPECTION': MaintenanceType.PREVENTIVE,
                }
                m_type = mtype_map.get((workorder.work_type or '').upper(), MaintenanceType.PREVENTIVE)
                maintenance_in = MaintenanceCreate(
                    description=workorder.title or f"WorkOrder {workorder.id}",
                    asset_id=workorder.asset_id,
                    user_id=workorder.assigned_to or workorder.created_by,
                    maintenance_type=m_type,
                    scheduled_date=workorder.scheduled_date,
                    completed_date=workorder.completed_date,
                    duration_hours=workorder.actual_hours,
                    cost=workorder.actual_cost,
                    notes=maintenance_notes,
                    workorder_id=workorder.id,
                    plan_id=getattr(workorder, 'plan_id', None)
                )
                maint = await create_maintenance(db=db, maintenance_in=maintenance_in)
                if _created_maintenance is not None:
                    _created_maintenance['maintenance'] = maint
                print(f"DEBUG: Maintenance creado para WO {workorder.id}")
            else:
                print(f"DEBUG: Ya existía maintenance para WO {workorder.id}, no se crea otro")
        except Exception as me:
            print(f"WARNING: Fallo creando maintenance automático para WO {workorder.id}: {me}")

    return workorder

async def delete_workorder(db: AsyncSession, workorder_id: int):
    """Delete a work order by ID"""
    result = await db.execute(
        select(WorkOrder).where(WorkOrder.id == workorder_id)
    )
    workorder = result.scalar_one_or_none()
    
    if workorder is None:
        return False
    
    await db.delete(workorder)
    await db.commit()
    return True