from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.maintenance import Maintenance
from app.schemas.maintenance import MaintenanceCreate, MaintenanceRead, MaintenanceUpdate
from datetime import datetime

async def create_maintenance(db: AsyncSession, maintenance_in: MaintenanceCreate):
    """Create a new maintenance record"""
    new_maintenance = Maintenance(
        asset_id=maintenance_in.asset_id,
        user_id=maintenance_in.user_id,
        description=maintenance_in.description,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_maintenance)
    await db.commit()
    await db.refresh(new_maintenance)
    return new_maintenance

async def get_maintenance(db: AsyncSession, maintenance_id: int):
    """Get a maintenance record by ID"""
    result = await db.execute(select(Maintenance).where(Maintenance.id == maintenance_id))
    return result.scalar_one_or_none()

async def get_all_maintenance(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all maintenance records with pagination"""
    result = await db.execute(select(Maintenance).offset(skip).limit(limit))
    return result.scalars().all()

async def get_maintenance_by_asset(db: AsyncSession, asset_id: int):
    """Get all maintenance records for a specific asset"""
    result = await db.execute(select(Maintenance).where(Maintenance.asset_id == asset_id))
    return result.scalars().all()

async def update_maintenance(db: AsyncSession, maintenance_id: int, maintenance_in: MaintenanceUpdate):
    """Update a maintenance record"""
    result = await db.execute(select(Maintenance).where(Maintenance.id == maintenance_id))
    maintenance = result.scalar_one_or_none()
    
    if maintenance is None:
        return None
    
    # Update only fields that are provided
    update_data = maintenance_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(maintenance, key, value)
    
    # Update the updated_at timestamp
    maintenance.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(maintenance)
    return maintenance

async def delete_maintenance(db: AsyncSession, maintenance_id: int):
    """Delete a maintenance record"""
    result = await db.execute(select(Maintenance).where(Maintenance.id == maintenance_id))
    maintenance = result.scalar_one_or_none()
    
    if maintenance is None:
        return False
    
    await db.delete(maintenance)
    await db.commit()
    return True