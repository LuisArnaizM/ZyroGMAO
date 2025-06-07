from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database.postgres import get_db
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.controllers.task import (
    create_task,
    get_task,
    get_tasks,
    get_tasks_by_user,
    get_tasks_by_workorder,
    update_task,
    delete_task
)
from app.auth.dependencies import get_current_user, require_role, get_current_organization

router = APIRouter(tags=["Tasks"])

@router.post("/", response_model=TaskRead)
async def create_new_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"])),
    organization = Depends(get_current_organization)
):
    return await create_task(
        db=db,
        task_in=task_in,
        created_by_id=user.id,
        organization_id=organization.id
    )

@router.get("/{task_id}", response_model=TaskRead)
async def read_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    organization = Depends(get_current_organization)
):
    task = await get_task(db=db, task_id=task_id, organization_id=organization.id)
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
    organization = Depends(get_current_organization)
):
    return await get_tasks(
        db=db,
        organization_id=organization.id,
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
    db: AsyncSession = Depends(get_db),
    organization = Depends(get_current_organization)
):
    return await get_tasks_by_user(db=db, user_id=user_id, organization_id=organization.id)

@router.get("/workorder/{workorder_id}", response_model=List[TaskRead])
async def read_tasks_by_workorder(
    workorder_id: int,
    db: AsyncSession = Depends(get_db),
    organization = Depends(get_current_organization)
):
    return await get_tasks_by_workorder(db=db, workorder_id=workorder_id, organization_id=organization.id)

@router.put("/{task_id}", response_model=TaskRead)
async def update_existing_task(
    task_id: int,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor", "Tecnico"])),
    organization = Depends(get_current_organization)
):
    task = await update_task(
        db=db,
        task_id=task_id,
        task_in=task_in,
        organization_id=organization.id
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}", response_model=dict)
async def delete_existing_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"])),
    organization = Depends(get_current_organization)
):
    result = await delete_task(db=db, task_id=task_id, organization_id=organization.id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"detail": "Task deleted successfully"}