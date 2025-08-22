from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.inventory import (
    InventoryItemCreate, InventoryItemRead, InventoryItemUpdate,
    AdjustQuantityRequest, TaskUsedComponentRead, InventoryItemReadWithComponent
)
from app.controllers.inventory import (
    create_inventory_item, get_inventory_items, get_inventory_item,
    update_inventory_item, delete_inventory_item, adjust_inventory_quantity,
    get_inventory_by_component, list_task_used_components
)


router = APIRouter(tags=["Inventory"])


@router.post("/", response_model=InventoryItemRead)
async def create_item(
    item_in: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await create_inventory_item(db, item_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[InventoryItemReadWithComponent])
async def list_items(
    component_type: Optional[str] = Query(None, description="Filtrar por tipo de componente"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_inventory_items(db, component_type)


@router.get("/{item_id}", response_model=InventoryItemReadWithComponent)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = await get_inventory_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.get("/by-component/{component_id}", response_model=InventoryItemReadWithComponent)
async def get_item_by_component(
    component_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = await get_inventory_by_component(db, component_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.put("/{item_id}", response_model=InventoryItemRead)
async def update_item(
    item_id: int,
    item_in: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = await update_inventory_item(db, item_id, item_in)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.delete("/{item_id}", response_model=dict)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ok = await delete_inventory_item(db, item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return {"status": "deleted"}


@router.post("/{item_id}/adjust", response_model=InventoryItemRead)
async def adjust_item_quantity(
    item_id: int,
    payload: AdjustQuantityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        item = await adjust_inventory_quantity(db, item_id, payload.delta)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/usage/", response_model=List[TaskUsedComponentRead])
async def list_usage(
    component_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await list_task_used_components(db, component_id)
