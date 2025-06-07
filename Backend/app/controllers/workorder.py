from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.workorder import WorkOrder
from app.models.asset import Asset
from app.models.failure import Failure
from app.schemas.workorder import WorkOrderCreate, WorkOrderRead, WorkOrderUpdate
from datetime import datetime

async def create_workorder(db: AsyncSession, workorder_in: WorkOrderCreate, created_by: int, organization_id: int):
    """Create a new work order"""
    
    # Verificar que el asset existe en la organización
    asset = await db.execute(
        select(Asset).where(
            Asset.id == workorder_in.asset_id,
            Asset.organization_id == organization_id
        )
    )
    if not asset.scalar_one_or_none():
        raise ValueError(f"Asset with ID {workorder_in.asset_id} does not exist in this organization")
    
    # Verificar failure si se proporciona
    if workorder_in.failure_id:
        failure = await db.execute(
            select(Failure).where(
                Failure.id == workorder_in.failure_id,
                Failure.organization_id == organization_id
            )
        )
        if not failure.scalar_one_or_none():
            raise ValueError(f"Failure with ID {workorder_in.failure_id} does not exist in this organization")
    
    workorder_data = workorder_in.model_dump()
    workorder_data['created_by'] = created_by
    workorder_data['organization_id'] = organization_id
    
    new_workorder = WorkOrder(**workorder_data)
    db.add(new_workorder)
    await db.commit()
    await db.refresh(new_workorder)
    return new_workorder

async def get_workorder(db: AsyncSession, workorder_id: int, organization_id: int):
    """Get a work order by ID within organization"""
    result = await db.execute(
        select(WorkOrder).where(
            WorkOrder.id == workorder_id,
            WorkOrder.organization_id == organization_id
        )
    )
    return result.scalar_one_or_none()

async def get_workorders(
    db: AsyncSession,
    organization_id: int,
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    status: str = None,
    work_type: str = None,
    priority: str = None,
    assigned_to: int = None
):
    """Get all work orders with filters, pagination and search capability within organization"""
    offset = (page - 1) * page_size
    
    query = select(WorkOrder).where(WorkOrder.organization_id == organization_id)
    
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

async def get_workorders_by_asset(db: AsyncSession, asset_id: int, organization_id: int):
    """Get all work orders for a specific asset within organization"""
    result = await db.execute(
        select(WorkOrder).where(
            WorkOrder.asset_id == asset_id,
            WorkOrder.organization_id == organization_id
        ).order_by(WorkOrder.created_at.desc())
    )
    return result.scalars().all()

async def get_workorders_by_user(db: AsyncSession, user_id: int, organization_id: int):
    """Get all work orders assigned to a specific user within organization"""
    result = await db.execute(
        select(WorkOrder).where(
            WorkOrder.assigned_to == user_id,
            WorkOrder.organization_id == organization_id
        ).order_by(WorkOrder.scheduled_date.asc())
    )
    return result.scalars().all()

async def update_workorder(db: AsyncSession, workorder_id: int, workorder_in: WorkOrderUpdate, organization_id: int):
    """Update a work order by ID within organization"""
    result = await db.execute(
        select(WorkOrder).where(
            WorkOrder.id == workorder_id,
            WorkOrder.organization_id == organization_id
        )
    )
    workorder = result.scalar_one_or_none()
    
    if workorder is None:
        return None
    
    update_data = workorder_in.model_dump(exclude_unset=True)
    
    # Lógica para fechas automáticas
    if update_data.get('status') == 'in_progress' and not workorder.started_date:
        update_data['started_date'] = datetime.utcnow()
    elif update_data.get('status') == 'completed' and not workorder.completed_date:
        update_data['completed_date'] = datetime.utcnow()
    
    for key, value in update_data.items():
        setattr(workorder, key, value)
    
    workorder.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(workorder)
    return workorder

async def delete_workorder(db: AsyncSession, workorder_id: int, organization_id: int):
    """Delete a work order by ID within organization"""
    result = await db.execute(
        select(WorkOrder).where(
            WorkOrder.id == workorder_id,
            WorkOrder.organization_id == organization_id
        )
    )
    workorder = result.scalar_one_or_none()
    
    if workorder is None:
        return False
    
    await db.delete(workorder)
    await db.commit()
    return True