from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.workorder import WorkOrder
from app.models.asset import Asset
from app.models.failure import Failure
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

async def update_workorder(db: AsyncSession, workorder_id: int, workorder_in: WorkOrderUpdate):
    """Update a work order by ID"""
    result = await db.execute(
        select(WorkOrder).where(WorkOrder.id == workorder_id)
    )
    workorder = result.scalar_one_or_none()
    
    if workorder is None:
        return None
    
    update_data = workorder_in.model_dump(exclude_unset=True)

    def to_naive_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    
    # Lógica para fechas automáticas
    if update_data.get('status') == 'in_progress' and not workorder.started_date:
        update_data['started_date'] = datetime.now(timezone.utc)
    elif update_data.get('status') == 'completed' and not workorder.completed_date:
        update_data['completed_date'] = datetime.now(timezone.utc)

    # Normalize possible provided datetime fields
    if 'scheduled_date' in update_data:
        update_data['scheduled_date'] = to_naive_utc(update_data['scheduled_date'])
    if 'started_date' in update_data and isinstance(update_data['started_date'], datetime):
        update_data['started_date'] = to_naive_utc(update_data['started_date'])
    if 'completed_date' in update_data and isinstance(update_data['completed_date'], datetime):
        update_data['completed_date'] = to_naive_utc(update_data['completed_date'])
    
    # Validación de asignación por departamento: si se establece assigned_to, comprobar que el usuario pertenece al mismo departamento (o subárbol) de workorder.department_id si existe
    if 'assigned_to' in update_data and update_data['assigned_to'] is not None:
        # Determinar el department objetivo
        target_dep_id = update_data.get('department_id', workorder.department_id)
        if target_dep_id is not None:
            # construir subárbol
            deps_result = await db.execute(select(Department))
            deps = deps_result.scalars().all()
            by_parent = {}
            for d in deps:
                by_parent.setdefault(d.parent_id, []).append(d.id)
            to_visit = [target_dep_id]
            subtree = set()
            while to_visit:
                cur = to_visit.pop()
                subtree.add(cur)
                to_visit.extend(by_parent.get(cur, []))
            # obtener usuario asignado
            user_q = await db.execute(select(User).where(User.id == update_data['assigned_to']))
            assigned_user = user_q.scalar_one_or_none()
            if not assigned_user:
                raise ValueError("Assigned user does not exist")

            # Además de comprobar department_id, permitir asignar si el usuario es manager
            # de algún departamento dentro del subárbol (department.manager_id) o si tiene
            # rol de Admin/Supervisor.
            manager_ids = set(d.manager_id for d in deps if d.id in subtree and d.manager_id is not None)
            user_role = getattr(assigned_user, 'role', None)
            if not (
                (assigned_user.department_id in subtree) or
                (assigned_user.id in manager_ids) or
                (user_role in ("Admin", "Supervisor"))
            ):
                raise ValueError("Assigned user does not belong to target department subtree or have sufficient role")

    for key, value in update_data.items():
        setattr(workorder, key, value)
    
    workorder.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(workorder)
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