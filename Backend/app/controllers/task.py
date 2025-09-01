from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.task import Task
from app.models.asset import Asset
from app.models.component import Component
from app.models.workorder import WorkOrder
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, TaskCompleteRequest, TaskUsedComponentIn
from app.models.inventory import InventoryItem, TaskUsedComponent
from app.models.enums import TaskStatus
from datetime import datetime, timezone, timedelta


def _naive_utc(dt: datetime | None) -> datetime | None:
    """Convierte cualquier datetime a naive UTC (sin tzinfo) para columnas TIMESTAMP WITHOUT TIME ZONE.

    - Si viene con tz -> se convierte a UTC y se quita tzinfo
    - Si viene naive -> se asume ya en UTC y se deja igual
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

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
    # Normalizar due_date (columna sin timezone) para evitar mezcla aware/naive
    if task_data.get("due_date") is not None:
        task_data["due_date"] = _naive_utc(task_data["due_date"])
    task_data['created_by_id'] = created_by_id
    
    # Si assigned_to y el creador es supervisor, validar jerarquía
    if task_data.get("assigned_to"):
        # Cargar creador
        from app.models.user import User
        from app.models.department import Department
        creator_res = await db.execute(select(User).where(User.id == created_by_id))
        creator = creator_res.scalar_one_or_none()
        if creator and creator.role == "Supervisor":
            # Obtener deps que gestiona
            dep_res = await db.execute(select(Department).where(Department.manager_id == created_by_id))
            managed = dep_res.scalars().all()
            if managed:
                # construir set de departamentos bajo su gestión
                all_deps_res = await db.execute(select(Department))
                all_deps = all_deps_res.scalars().all()
                by_parent = {}
                for d in all_deps:
                    by_parent.setdefault(d.parent_id, []).append(d)
                target = set()
                stack = [d.id for d in managed]
                while stack:
                    cur = stack.pop()
                    if cur in target:
                        continue
                    target.add(cur)
                    for ch in by_parent.get(cur, []):
                        stack.append(ch.id)
                # Usuario asignado
                assigned_res = await db.execute(select(User).where(User.id == task_data["assigned_to"]))
                assigned_user = assigned_res.scalar_one_or_none()
                if not assigned_user or assigned_user.department_id not in target:
                    raise ValueError("Supervisor cannot assign task to user outside managed departments")
        # Validar día laborable si due_date
        if task_data.get("due_date"):
            from datetime import date as _date
            from app.controllers.calendar import is_non_working
            assigned_id = task_data["assigned_to"]
            due_d = task_data["due_date"].date() if hasattr(task_data["due_date"], 'date') else task_data["due_date"]
            if await is_non_working(db, assigned_id, due_d):
                raise ValueError("Cannot assign task on non-working day for user")
            # Validar no exceder capacidad diaria (si estimated_hours)
            if task_data.get("estimated_hours"):
                from app.controllers.calendar import compute_capacity_week
                # capacidad del día: compute_capacity_week(due_d,1)
                cap_rows = await compute_capacity_week(db, task_data["assigned_to"], due_d, 1)
                cap_hours = cap_rows[0][1]
                # sumar horas ya planificadas ese día
                existing_q = await db.execute(
                    select(Task).where(
                        Task.assigned_to == task_data["assigned_to"],
                        Task.due_date >= task_data["due_date"].replace(hour=0, minute=0, second=0, microsecond=0),
                        Task.due_date <  task_data["due_date"].replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1),
                    )
                )
                existing_tasks = existing_q.scalars().all()
                planned = sum(filter(None, [t.estimated_hours or 0 for t in existing_tasks]))
                if planned + float(task_data["estimated_hours"]) - 1e-6 > cap_hours and cap_hours > 0:
                    raise ValueError("Daily capacity exceeded for user on that date")
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
    # Normalizar due_date si viene en update
    if "due_date" in update_data:
        update_data["due_date"] = _naive_utc(update_data["due_date"])

    # Validar no asignar en día no laborable si cambia due_date o assigned_to (o ambos)
    maybe_due = update_data.get("due_date", task.due_date)
    maybe_assigned = update_data.get("assigned_to", task.assigned_to)
    if maybe_due and maybe_assigned:
        try:
            from app.controllers.calendar import is_non_working  # import local para evitar ciclos tempranos
            due_d = maybe_due.date() if hasattr(maybe_due, 'date') else maybe_due
            if await is_non_working(db, maybe_assigned, due_d):
                raise ValueError("Cannot assign/update task on non-working day for user")
            # Validar capacidad si cambia estimated_hours, due_date o assigned_to
            if any(k in update_data for k in ("estimated_hours", "due_date", "assigned_to")) and (update_data.get("estimated_hours") or task.estimated_hours):
                from app.controllers.calendar import compute_capacity_week
                cap_rows = await compute_capacity_week(db, maybe_assigned, due_d, 1)
                cap_hours = cap_rows[0][1]
                # Query tareas día
                start_day = maybe_due.replace(hour=0, minute=0, second=0, microsecond=0)
                end_day = start_day + timedelta(days=1)
                existing_q = await db.execute(
                    select(Task).where(
                        Task.assigned_to == maybe_assigned,
                        Task.due_date >= start_day,
                        Task.due_date < end_day,
                        Task.id != task.id,
                    )
                )
                existing_tasks = existing_q.scalars().all()
                planned = sum(filter(None, [t.estimated_hours or 0 for t in existing_tasks]))
                new_est = update_data.get("estimated_hours", task.estimated_hours) or 0
                if cap_hours > 0 and planned + float(new_est) - 1e-6 > cap_hours:
                    raise ValueError("Daily capacity exceeded for user on that date")
        except ModuleNotFoundError:
            # Si el módulo de calendario no existe (deployment antiguo) ignorar validación
            pass
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