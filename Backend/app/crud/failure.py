from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.failure import MaintenanceRequest
from app.schemas.failure import MaintenanceCreate, MaintenanceRead, MaintenanceUpdate

async def create_maintenance(db: AsyncSession, failure: MaintenanceCreate):
    """Create a new maintenance request"""
    new_maintenance = MaintenanceRequest(
        asset_id=failure.asset_id,
        description=failure.description,
        status="open"
    )
    db.add(new_maintenance)
    await db.commit()
    await db.refresh(new_maintenance)
    return new_maintenance

async def get_maintenance(db: AsyncSession, failure_id: int):
    """Get a maintenance request by ID"""
    result = await db.execute(
        select(MaintenanceRequest).where(MaintenanceRequest.id == failure_id)
    )
    return result.scalar_one_or_none()

async def get_all_maintenance(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all maintenance requests with pagination"""
    result = await db.execute(
        select(MaintenanceRequest).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def update_maintenance(db: AsyncSession, failure_id: int, failure: MaintenanceUpdate):
    """Update a maintenance request"""
    result = await db.execute(
        select(MaintenanceRequest).where(MaintenanceRequest.id == failure_id)
    )
    maintenance = result.scalar_one_or_none()
    
    if maintenance is None:
        return None
        
    # Update fields
    if failure.description:
        maintenance.description = failure.description
    if failure.status:
        maintenance.status = failure.status
        
    await db.commit()
    await db.refresh(maintenance)
    return maintenance

async def delete_maintenance(db: AsyncSession, failure_id: int):
    """Delete a maintenance request"""
    result = await db.execute(
        select(MaintenanceRequest).where(MaintenanceRequest.id == failure_id)
    )
    maintenance = result.scalar_one_or_none()
    
    if maintenance is None:
        return False
        
    await db.delete(maintenance)
    await db.commit()
    return True