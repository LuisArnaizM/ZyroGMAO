from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.maintenance import Maintenance
from app.schemas.maintenance import MaintenanceCreate, MaintenanceRead, MaintenanceUpdate
from datetime import datetime, timezone

async def create_maintenance(db: AsyncSession, maintenance_in: MaintenanceCreate):
    """Create a new maintenance record"""
    def _to_naive_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    m_type = maintenance_in.maintenance_type.value if hasattr(maintenance_in.maintenance_type, 'value') else maintenance_in.maintenance_type
    scheduled_dt = _to_naive_utc(maintenance_in.scheduled_date)
    completed_dt = _to_naive_utc(maintenance_in.completed_date if hasattr(maintenance_in, 'completed_date') else None)
    new_maintenance = Maintenance(
        asset_id=maintenance_in.asset_id,
        user_id=maintenance_in.user_id,
        description=maintenance_in.description,
        maintenance_type=m_type,
    scheduled_date=scheduled_dt,
    completed_date=completed_dt,
    duration_hours=maintenance_in.duration_hours,
    cost=maintenance_in.cost,
    notes=maintenance_in.notes,
    workorder_id=maintenance_in.workorder_id,
    component_id=maintenance_in.component_id,
    plan_id=maintenance_in.plan_id,
        status="SCHEDULED",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(new_maintenance)
    await db.commit()
    await db.refresh(new_maintenance)
    return new_maintenance

async def get_maintenance(db: AsyncSession, maintenance_id: int):
    """Get a maintenance record by ID within organization"""
    result = await db.execute(
    select(Maintenance).where(Maintenance.id == maintenance_id)
    )
    return result.scalar_one_or_none()

async def get_all_maintenance(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str = None
):
    """Get all maintenance records with pagination and optional search"""
    offset = (page - 1) * page_size
    
    query = select(Maintenance)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Maintenance.description.ilike(search_term)) | 
            (Maintenance.status.ilike(search_term))
        )
    
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()

async def get_maintenance_by_asset(db: AsyncSession, asset_id: int):
    """Get all maintenance records for a specific asset"""
    result = await db.execute(
        select(Maintenance).where(Maintenance.asset_id == asset_id)
    )
    return result.scalars().all()

async def update_maintenance(db: AsyncSession, maintenance_id: int, maintenance_in: MaintenanceUpdate):
    """Update a maintenance record"""
    result = await db.execute(
        select(Maintenance).where(Maintenance.id == maintenance_id)
    )
    maintenance = result.scalar_one_or_none()
    
    if maintenance is None:
        return None
    
    update_data = maintenance_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(maintenance, key, value)
    
    maintenance.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(maintenance)
    return maintenance

async def delete_maintenance(db: AsyncSession, maintenance_id: int):
    """Delete a maintenance record"""
    result = await db.execute(
        select(Maintenance).where(Maintenance.id == maintenance_id)
    )
    maintenance = result.scalar_one_or_none()
    
    if maintenance is None:
        return False
    
    await db.delete(maintenance)
    await db.commit()
    return True