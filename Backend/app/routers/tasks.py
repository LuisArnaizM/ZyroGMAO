from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database.postgres import get_db
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, TaskCompleteRequest
from app.controllers.task import (
    create_task,
    get_task,
    get_tasks,
    get_tasks_by_user,
    get_tasks_by_workorder,
    update_task,
    complete_task,
    delete_task
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(tags=["Tasks"])

@router.post("/", response_model=TaskRead)
async def create_new_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"])),
    # Organización eliminada
):
    try:
        return await create_task(
            db=db,
            task_in=task_in,
            created_by_id=user["id"],
        )
    except ValueError as e:
        # Errores de validación de referencias (asset/component/workorder inexistente)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{task_id}", response_model=TaskRead)
async def read_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    task = await get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/", response_model=List[TaskRead])
async def read_tasks(
    page: int = Query(1, ge=1, description="Página actual"),
    page_size: int = Query(20, ge=1, le=100, description="Número de elementos por página"),
    search: str = Query(None, description="Término de búsqueda para filtrar tareas"),
    status: str = Query(None, description="Filtrar por estado"),
    priority: str = Query(None, description="Filtrar por prioridad"),
    assigned_to: int = Query(None, description="Filtrar por usuario asignado"),
    db: AsyncSession = Depends(get_db),
    _user = Depends(require_role(["Admin", "Supervisor"]))
):
    return await get_tasks(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        priority=priority,
        assigned_to=assigned_to
    )

@router.get("/user/{user_id}", response_model=List[TaskRead])
async def read_tasks_by_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_tasks_by_user(db=db, user_id=user_id)

@router.get("/workorder/{workorder_id}", response_model=List[TaskRead])
async def read_tasks_by_workorder(
    workorder_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    # Si el usuario es técnico, limitar acceso a tareas de workorders dentro de su subárbol de departamento
    if user["role"] == "Tecnico":
        from sqlalchemy.future import select
        from app.models.workorder import WorkOrder
        from app.models.department import Department
        # Obtener workorder
        result = await db.execute(select(WorkOrder).where(WorkOrder.id == workorder_id))
        wo = result.scalar_one_or_none()
        if not wo:
            return []
        # Si la WO no tiene department_id, negar
        if wo.department_id is None:
            return []
        # Construir subárbol del departamento del técnico
        deps_result = await db.execute(select(Department))
        deps = deps_result.scalars().all()
        by_parent = {}
        for d in deps:
            by_parent.setdefault(d.parent_id, []).append(d.id)
        to_visit = [user.get("department_id")] if user.get("department_id") else []
        subtree = set()
        while to_visit:
            cur = to_visit.pop()
            if cur is None:
                continue
            subtree.add(cur)
            to_visit.extend(by_parent.get(cur, []))
        if wo.department_id not in subtree:
            return []
    return await get_tasks_by_workorder(db=db, workorder_id=workorder_id)

@router.put("/{task_id}", response_model=TaskRead)
async def update_existing_task(
    task_id: int,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    task = await update_task(
        db=db,
        task_id=task_id,
        task_in=task_in,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}", response_model=TaskRead)
async def patch_task(
    task_id: int,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    # Técnicos: solo pueden completar tareas propias y añadir actual_hours/completion_notes/description
    if user["role"] == "Tecnico":
        # Cargar tarea y validar ownership/org
        task = await get_task(db=db, task_id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.assigned_to != user["id"]:
            raise HTTPException(status_code=403, detail="Not allowed")
        allowed_fields = {"status", "actual_hours", "completion_notes", "description"}
        update_payload = task_in.model_dump(exclude_unset=True)
        if not set(update_payload.keys()).issubset(allowed_fields):
            raise HTTPException(status_code=403, detail="Technicians can only complete and add actual hours/notes")
    else:
        # Admin/Supervisor pasan el require_role en update controller, aquí permitimos patch general
        pass

    task = await update_task(db=db, task_id=task_id, task_in=task_in)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}", response_model=dict)
async def delete_existing_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    result = await delete_task(db=db, task_id=task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"detail": "Task deleted successfully"}


@router.post("/{task_id}/complete", response_model=TaskRead)
async def complete_task_endpoint(
    task_id: int,
    payload: TaskCompleteRequest,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    # Permisos: Técnicos solo sus tareas; Admin/Supervisor cualquiera
    task = await get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if user["role"] == "Tecnico" and task.assigned_to != user["id"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    try:
        updated = await complete_task(db=db, task_id=task_id, data=payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated