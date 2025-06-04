from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.postgres import get_db
from app.schemas.machine import MachineCreate, MachineRead, MachineUpdate
from app.controllers.machine import (
    create_machine, 
    get_machine, 
    get_machines, 
    update_machine, 
    delete_machine
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/machines", tags=["Machines"])

@router.post("/", response_model=MachineRead)
async def create_new_machine(
    machine_in: MachineCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    return await create_machine(db=db, machine_in=machine_in)

@router.get("/{machine_id}", response_model=MachineRead)
async def read_machine(
    machine_id: int,
    db: AsyncSession = Depends(get_db)
):
    machine = await get_machine(db=db, machine_id=machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

@router.get("/", response_model=List[MachineRead])
async def read_machines(
    page: int = Query(1, ge=1, description="Página actual"),
    page_size: int = Query(20, ge=1, le=100, description="Número de elementos por página"),
    search: str = Query(None, description="Término de búsqueda para filtrar activos"),
    db: AsyncSession = Depends(get_db)
):
    return await get_machines(db=db, page=page, page_size=page_size, search=search)

@router.put("/{machine_id}", response_model=MachineRead)
async def update_existing_machine(
    machine_id: int,
    machine_in: MachineUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    machine = await update_machine(db=db, machine_id=machine_id, machine_in=machine_in)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

@router.delete("/{machine_id}", response_model=dict)
async def delete_existing_machine(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin"]))
):
    result = await delete_machine(db=db, machine_id=machine_id)
    if not result:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {"detail": "Machine deleted successfully"}