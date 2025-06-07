from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.task import Task
from app.models.asset import Asset
from app.models.component import Component
from app.models.workorder import WorkOrder
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from datetime import datetime

async def create_task(db: AsyncSession, task_in: TaskCreate, created_by_id: int, organization_id: int):
    """Create a new task"""
    
    # Verificar referencias opcionales
    if task_in.asset_id:
        asset = await db.execute(
            select(Asset).where(
                Asset.id == task_in.asset_id,
                Asset.organization_id == organization_id
            )
        )
        if not asset.scalar_one_or_none():
            raise ValueError(f"Asset with ID {task_in.asset_id} does not exist in this organization")
    
    if task_in.component_id:
        component = await db.execute(
            select(Component).where(
                Component.id == task_in.component_id,
                Component.organization_id == organization_id
            )
        )
        if not component.scalar_one_or_none():
            raise ValueError(f"Component with ID {task_in.component_id} does not exist in this organization")
    
    if task_in.workorder_id:
        workorder = await db.execute(
            select(WorkOrder).where(
                WorkOrder.id == task_in.workorder_id,
                WorkOrder.organization_id == organization_id
            )
        )
        if not workorder.scalar_one_or_none():
            raise ValueError(f"WorkOrder with ID {task_in.workorder_id} does not exist in this organization")
    
    task_data = task_in.model_dump()
    task_data['created_by_id'] = created_by_id
    task_data['organization_id'] = organization_id
    
    new_task = Task(**task_data)
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task

async def get_task(db: AsyncSession, task_id: int, organization_id: int):
    """Get a task by ID within organization"""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.organization_id == organization_id
        )
    )
    return result.scalar_one_or_none()

async def get_tasks(
    db: AsyncSession,
    organization_id: int,
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    status: str = None,
    priority: str = None,
    assigned_to: int = None
):
    """Get all tasks with filters, pagination and search capability within organization"""
    offset = (page - 1) * page_size
    
    query = select(Task).where(Task.organization_id == organization_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Task.title.ilike(search_term)) |
            (Task.description.ilike(search_term))
        )
    
    if status:
        query = query.where(Task.status == status)
    
    if priority:
        query = query.where(Task.priority == priority)
    
    if assigned_to:
        query = query.where(Task.assigned_to == assigned_to)
    
    query = query.offset(offset).limit(page_size).order_by(Task.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def get_tasks_by_user(db: AsyncSession, user_id: int, organization_id: int):
    """Get all tasks assigned to a specific user within organization"""
    result = await db.execute(
        select(Task).where(
            Task.assigned_to == user_id,
            Task.organization_id == organization_id
        ).order_by(Task.due_date.asc())
    )
    return result.scalars().all()

async def get_tasks_by_workorder(db: AsyncSession, workorder_id: int, organization_id: int):
    """Get all tasks for a specific workorder within organization"""
    result = await db.execute(
        select(Task).where(
            Task.workorder_id == workorder_id,
            Task.organization_id == organization_id
        ).order_by(Task.created_at.desc())
    )
    return result.scalars().all()

async def update_task(db: AsyncSession, task_id: int, task_in: TaskUpdate, organization_id: int):
    """Update a task by ID within organization"""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.organization_id == organization_id
        )
    )
    task = result.scalar_one_or_none()
    
    if task is None:
        return None
    
    update_data = task_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    task.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(task)
    return task

async def delete_task(db: AsyncSession, task_id: int, organization_id: int):
    """Delete a task by ID within organization"""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.organization_id == organization_id
        )
    )
    task = result.scalar_one_or_none()
    
    if task is None:
        return False
    
    await db.delete(task)
    await db.commit()
    return True