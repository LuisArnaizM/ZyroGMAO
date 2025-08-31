from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.component import Component
from app.models.asset import Asset
from app.schemas.component import ComponentCreate, ComponentUpdate
from typing import List, Optional

async def create_component(db: AsyncSession, component_in: ComponentCreate):
    """Crear un nuevo componente"""
    
    # Verificar que el asset existe y pertenece a la organización
    stmt = select(Asset).where(Asset.id == component_in.asset_id)
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise ValueError(f"Asset with ID {component_in.asset_id} does not exist")
    
    # Crear el componente
    component_data = component_in.model_dump()
    
    db_component = Component(**component_data)
    db.add(db_component)
    await db.commit()
    await db.refresh(db_component)
    
    return db_component

async def get_components(db: AsyncSession, asset_id: Optional[int] = None, 
                       skip: int = 0, limit: int = 100) -> List[Component]:
    """Obtener componentes con filtros opcionales"""
    
    stmt = select(Component)
    
    if asset_id:
        stmt = stmt.where(Component.asset_id == asset_id)
    
    stmt = stmt.options(
        selectinload(Component.asset),
        selectinload(Component.responsible)
    ).offset(skip).limit(limit).order_by(Component.created_at.desc())
    
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_component(db: AsyncSession, component_id: int):
    """Obtener un componente específico"""
    
    stmt = select(Component).where(
        Component.id == component_id
    ).options(
        selectinload(Component.asset),
        selectinload(Component.responsible),
        selectinload(Component.failures),
        selectinload(Component.maintenance_records),
        selectinload(Component.tasks)
    )
    
    result = await db.execute(stmt)
    component = result.scalar_one_or_none()
    
    if not component:
        raise ValueError(f"Component with ID {component_id} not found")
    
    return component

async def update_component(db: AsyncSession, component_id: int, component_in: ComponentUpdate):
    """Actualizar un componente"""
    
    stmt = select(Component).where(Component.id == component_id)
    result = await db.execute(stmt)
    db_component = result.scalar_one_or_none()
    
    if not db_component:
        raise ValueError(f"Component with ID {component_id} not found")
    
    # Actualizar campos
    update_data = component_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_component, field, value)
    
    await db.commit()
    await db.refresh(db_component)
    
    return db_component

async def delete_component(db: AsyncSession, component_id: int):
    """Eliminar un componente"""
    
    stmt = select(Component).where(Component.id == component_id)
    result = await db.execute(stmt)
    db_component = result.scalar_one_or_none()
    
    if not db_component:
        raise ValueError(f"Component with ID {component_id} not found")
    
    await db.delete(db_component)
    await db.commit()
    
    return {"message": "Component deleted successfully"}

async def get_components_by_asset(db: AsyncSession, asset_id: int) -> List[Component]:
    """Obtener todos los componentes de un asset específico"""
    
    # Verificar que el asset existe y pertenece a la organización
    stmt = select(Asset).where(Asset.id == asset_id)
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise ValueError(f"Asset with ID {asset_id} does not exist")
    
    return await get_components(db, asset_id=asset_id)

async def get_component_statistics(db: AsyncSession, component_id: int):
    """Obtener estadísticas de un componente"""
    
    component = await get_component(db, component_id)
    
    stats = {
        "component_id": component_id,
        "total_failures": len(component.failures) if component.failures else 0,
        "total_maintenance_records": len(component.maintenance_records) if component.maintenance_records else 0,
        "total_tasks": len(component.tasks) if component.tasks else 0,
        "status": component.status,
        "needs_maintenance": False  # Lógica personalizable
    }
    
    # Calcular si necesita mantenimiento
    if component.maintenance_interval_days and component.last_maintenance_date:
        from datetime import datetime, timedelta
        days_since_maintenance = (datetime.now() - component.last_maintenance_date).days
        stats["days_since_last_maintenance"] = days_since_maintenance
        stats["needs_maintenance"] = days_since_maintenance >= component.maintenance_interval_days
    
    return stats
