from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.workorder import WorkOrder
from app.schemas.workorder import WorkOrderCreate, WorkOrderRead, WorkOrderUpdate
from datetime import datetime

async def create_workorder(db: AsyncSession, workorder_in: WorkOrderCreate, created_by: str):
    """Create a new work order"""
    new_workorder = WorkOrder(
        task_id=workorder_in.task_id,
        maintenance_id=workorder_in.maintenance_id,
        description=workorder_in.description,
        status=workorder_in.status,
        created_by=created_by,
        created_at=datetime.utcnow()
    )
    db.add(new_workorder)
    await db.commit()
    await db.refresh(new_workorder)
    return new_workorder

async def get_workorder(db: AsyncSession, workorder_id: int):
    """Get a work order by ID"""
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == workorder_id))
    return result.scalar_one_or_none()

async def get_workorders(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all work orders with pagination"""
    result = await db.execute(select(WorkOrder).offset(skip).limit(limit))
    return result.scalars().all()

async def get_workorders_by_maintenance(db: AsyncSession, maintenance_id: int):
    """Get all work orders for a specific maintenance request"""
    result = await db.execute(
        select(WorkOrder).where(WorkOrder.maintenance_id == maintenance_id)
    )
    return result.scalars().all()

async def update_workorder(db: AsyncSession, workorder_id: int, workorder_in: WorkOrderUpdate):
    """Update a work order by ID"""
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == workorder_id))
    workorder = result.scalar_one_or_none()
    
    if workorder is None:
        return None
    
    # Update only fields that are provided
    update_data = workorder_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(workorder, key, value)
    
    # Update the updated_at timestamp
    workorder.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(workorder)
    return workorder

async def delete_workorder(db: AsyncSession, workorder_id: int):
    """Delete a work order by ID"""
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == workorder_id))
    workorder = result.scalar_one_or_none()
    
    if workorder is None:
        return False
    
    await db.delete(workorder)
    await db.commit()
    return True