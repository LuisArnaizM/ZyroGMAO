from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.models.inventory import InventoryItem, TaskUsedComponent
from app.models.component import Component
from app.schemas.inventory import InventoryItemCreate, InventoryItemUpdate


async def create_inventory_item(db: AsyncSession, item_in: InventoryItemCreate) -> InventoryItem:
    # Verificar componente existe
    comp_res = await db.execute(select(Component).where(Component.id == item_in.component_id))
    comp = comp_res.scalar_one_or_none()
    if comp is None:
        raise ValueError(f"Component {item_in.component_id} not found")

    # Evitar duplicados (1-1 con componente)
    exists_res = await db.execute(select(InventoryItem).where(InventoryItem.component_id == item_in.component_id))
    if exists_res.scalar_one_or_none():
        raise ValueError("Inventory item for this component already exists")

    item = InventoryItem(**item_in.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def get_inventory_items(db: AsyncSession, component_type: Optional[str] = None) -> List[InventoryItem]:
    query = select(InventoryItem).options(selectinload(InventoryItem.component))
    if component_type:
        query = query.join(Component).where(Component.component_type == component_type)
    res = await db.execute(query)
    return res.scalars().all()


async def get_inventory_item(db: AsyncSession, item_id: int) -> Optional[InventoryItem]:
    res = await db.execute(select(InventoryItem).options(selectinload(InventoryItem.component)).where(InventoryItem.id == item_id))
    return res.scalar_one_or_none()


async def get_inventory_by_component(db: AsyncSession, component_id: int) -> Optional[InventoryItem]:
    res = await db.execute(select(InventoryItem).options(selectinload(InventoryItem.component)).where(InventoryItem.component_id == component_id))
    return res.scalar_one_or_none()


async def update_inventory_item(db: AsyncSession, item_id: int, item_in: InventoryItemUpdate) -> Optional[InventoryItem]:
    res = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = res.scalar_one_or_none()
    if not item:
        return None
    data = item_in.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_inventory_item(db: AsyncSession, item_id: int) -> bool:
    res = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = res.scalar_one_or_none()
    if not item:
        return False
    await db.delete(item)
    await db.commit()
    return True


async def adjust_inventory_quantity(db: AsyncSession, item_id: int, delta: float) -> Optional[InventoryItem]:
    res = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = res.scalar_one_or_none()
    if not item:
        return None
    new_q = (item.quantity or 0) + float(delta)
    if new_q < 0:
        raise ValueError("Stock cannot be negative")
    item.quantity = new_q
    await db.commit()
    await db.refresh(item)
    return item


async def list_task_used_components(db: AsyncSession, component_id: Optional[int] = None):
    query = select(TaskUsedComponent)
    if component_id:
        query = query.where(TaskUsedComponent.component_id == component_id)
    res = await db.execute(query)
    return res.scalars().all()
