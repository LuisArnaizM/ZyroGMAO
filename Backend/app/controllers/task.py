from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from datetime import datetime

async def create_task(db: AsyncSession, task_in: TaskCreate, created_by: str):
    """Create a new task"""
    new_task = Task(
        name=task_in.name,
        description=task_in.description,
        assigned_to=task_in.assigned_to,
        machine_id=task_in.machine_id,
        due_date=task_in.due_date,
        created_by=created_by,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task

async def get_task(db: AsyncSession, task_id: int):
    """Get a task by ID"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()

async def get_tasks(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str = None
):
    """
    Get all tasks with pagination and search capability
    
    Parameters:
    - db: Database session
    - page: Page number (starts from 1)
    - page_size: Number of records per page
    - search: Search string to filter tasks by name or description
    """
    # Calculate offset based on page and page_size
    offset = (page - 1) * page_size
    
    # Build the base query
    query = select(Task)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Task.name.ilike(search_term)) | 
            (Task.description.ilike(search_term))
        )
    
    # Apply pagination
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    return result.scalars().all()

async def update_task(db: AsyncSession, task_id: int, task_in: TaskUpdate):
    """Update a task by ID"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if task is None:
        return None
    
    # Update only the fields that are provided
    update_data = task_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    # Update the updated_at timestamp
    task.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(task)
    return task

async def delete_task(db: AsyncSession, task_id: int):
    """Delete a task by ID"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if task is None:
        return False
    
    await db.delete(task)
    await db.commit()
    return True