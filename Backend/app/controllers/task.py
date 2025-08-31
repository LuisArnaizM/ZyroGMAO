from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.task import Task
from app.models.asset import Asset
from app.models.component import Component
from app.models.workorder import WorkOrder
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, TaskCompleteRequest, TaskUsedComponentIn
from app.models.inventory import InventoryItem, TaskUsedComponent
from app.models.enums import TaskStatus
from datetime import datetime, timezone

async def create_task(db: AsyncSession, task_in: TaskCreate, created_by_id: int):
    """Create a new task"""
    
    # Verificar referencias opcionales
    if task_in.asset_id:
        asset = await db.execute(select(Asset).where(Asset.id == task_in.asset_id))
        if not asset.scalar_one_or_none():
            raise ValueError(f"Asset with ID {task_in.asset_id} does not exist")
    
    if task_in.component_id:
        component = await db.execute(select(Component).where(Component.id == task_in.component_id))
        if not component.scalar_one_or_none():
            raise ValueError(f"Component with ID {task_in.component_id} does not exist")
    
    if task_in.workorder_id:
        workorder = await db.execute(select(WorkOrder).where(WorkOrder.id == task_in.workorder_id))
        if not workorder.scalar_one_or_none():
            raise ValueError(f"WorkOrder with ID {task_in.workorder_id} does not exist")
    
    task_data = task_in.model_dump()
    task_data['created_by_id'] = created_by_id
    
    new_task = Task(**task_data)
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
    search: str = None,
    status: str = None,
    priority: str = None,
    assigned_to: int = None
):
    """Get all tasks with filters, pagination and search capability within organization"""
    offset = (page - 1) * page_size
    
    query = select(Task)
    
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

async def get_tasks_by_user(db: AsyncSession, user_id: int):
    """Get all tasks assigned to a specific user"""
    result = await db.execute(select(Task).where(Task.assigned_to == user_id).order_by(Task.due_date.asc()))
    return result.scalars().all()

async def get_tasks_by_workorder(db: AsyncSession, workorder_id: int):
    """Get all tasks for a specific workorder"""
    result = await db.execute(select(Task).where(Task.workorder_id == workorder_id).order_by(Task.created_at.desc()))
    return result.scalars().all()

async def update_task(db: AsyncSession, task_id: int, task_in: TaskUpdate):
    """Update a task by ID"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if task is None:
        return None
    
    update_data = task_in.model_dump(exclude_unset=True)
    # Procesar componentes usados si se completa la tarea
    used = update_data.pop("used_components", None)
    for key, value in update_data.items():
        setattr(task, key, value)

    # Si se proveen componentes usados, validar y descontar inventario
    if used:
        for item in used:
            comp_id = item["component_id"] if isinstance(item, dict) else item.component_id
            qty = float(item["quantity"] if isinstance(item, dict) else item.quantity)
            # Obtener inventario
            inv_res = await db.execute(select(InventoryItem).where(InventoryItem.component_id == comp_id))
            inv = inv_res.scalar_one_or_none()
            if inv is None or inv.quantity is None or inv.quantity < qty:
                raise ValueError(f"Insufficient inventory for component {comp_id}")
            # Descontar
            inv.quantity = inv.quantity - qty
            # Registrar uso
            tuc = TaskUsedComponent(
                task_id=task.id,
                component_id=comp_id,
                quantity=qty,
                unit_cost_snapshot=inv.unit_cost,
            )
            db.add(tuc)
    
    task.updated_at = datetime.now(timezone.utc)
    
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


async def complete_task(db: AsyncSession, task_id: int, data: TaskCompleteRequest):
    """Mark task as completed, attach notes/description/actual_hours and consume inventory via used_components."""
    # Cargar tarea para validar existencia
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        return None

    # Si ya está completada, no repetir
    if getattr(task, "status", None) == "COMPLETED":
        return task

    # Construir TaskUpdate
    used_list = None
    if data.used_components:
        # Mapear a TaskUsedComponentIn
        used_list = [
            TaskUsedComponentIn(component_id=item.component_id, quantity=item.quantity)
            for item in data.used_components
        ]

    update = TaskUpdate(
        status="COMPLETED",
        completion_notes=data.notes,
        description=data.description,
        actual_hours=data.actual_hours,
        used_components=used_list,
    )

    # Reutilizar la lógica existente de update_task (descuentos e inserción de TaskUsedComponent)
    return await update_task(db=db, task_id=task_id, task_in=update)