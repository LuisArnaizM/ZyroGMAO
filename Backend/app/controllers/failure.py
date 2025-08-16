from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.failure import Failure
from app.models.asset import Asset
from app.models.component import Component
from app.schemas.failure import FailureCreate, FailureRead, FailureUpdate
from datetime import datetime

async def create_failure(db: AsyncSession, failure_in: FailureCreate, reported_by: int, organization_id: int):
    """Create a new failure report"""
    
    # Validar que al menos uno de los IDs esté presente
    if not failure_in.asset_id and not failure_in.component_id:
        raise ValueError("Debe proporcionar asset_id o component_id")

    # Verificar que el asset o component existe en la organización
    if failure_in.asset_id:
        asset = await db.execute(
            select(Asset).where(
                Asset.id == failure_in.asset_id,
                Asset.organization_id == organization_id
            )
        )
        if not asset.scalar_one_or_none():
            raise ValueError(f"Asset with ID {failure_in.asset_id} does not exist in this organization")

    if failure_in.component_id:
        component = await db.execute(
            select(Component).where(
                Component.id == failure_in.component_id,
                Component.organization_id == organization_id
            )
        )
        if not component.scalar_one_or_none():
            raise ValueError(f"Component with ID {failure_in.component_id} does not exist in this organization")
    
    failure_data = failure_in.model_dump(exclude_none=True)
    failure_data['reported_by'] = reported_by
    failure_data['organization_id'] = organization_id
    failure_data['status'] = 'reported'
    
    new_failure = Failure(**failure_data)
    db.add(new_failure)
    await db.commit()
    await db.refresh(new_failure)
    return new_failure

async def get_failure(db: AsyncSession, failure_id: int, organization_id: int):
    """Get a failure by ID within organization"""
    result = await db.execute(
        select(Failure).where(
            Failure.id == failure_id,
            Failure.organization_id == organization_id
        )
    )
    return result.scalar_one_or_none()

async def get_failures(
    db: AsyncSession,
    organization_id: int,
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    status: str = None,
    severity: str = None
):
    """Get all failures with filters, pagination and search capability within organization"""
    offset = (page - 1) * page_size
    
    query = select(Failure).where(Failure.organization_id == organization_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Failure.description.ilike(search_term)) |
            (Failure.resolution_notes.ilike(search_term))
        )
    
    if status:
        query = query.where(Failure.status == status)
    
    if severity:
        query = query.where(Failure.severity == severity)
    
    query = query.offset(offset).limit(page_size).order_by(Failure.reported_date.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def get_failures_by_asset(db: AsyncSession, asset_id: int, organization_id: int):
    """Get all failures for a specific asset within organization"""
    result = await db.execute(
        select(Failure).where(
            Failure.asset_id == asset_id,
            Failure.organization_id == organization_id
        ).order_by(Failure.reported_date.desc())
    )
    return result.scalars().all()

async def update_failure(db: AsyncSession, failure_id: int, failure_in: FailureUpdate, organization_id: int):
    """Update a failure by ID within organization"""
    result = await db.execute(
        select(Failure).where(
            Failure.id == failure_id,
            Failure.organization_id == organization_id
        )
    )
    failure = result.scalar_one_or_none()
    
    if failure is None:
        return None
    
    update_data = failure_in.model_dump(exclude_unset=True)
    
    # Si se marca como resuelto y no tenía fecha de resolución, agregarla
    if update_data.get('status') == 'resolved' and not failure.resolved_date:
        update_data['resolved_date'] = datetime.utcnow()
    
    for key, value in update_data.items():
        setattr(failure, key, value)
    
    failure.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(failure)
    return failure

async def delete_failure(db: AsyncSession, failure_id: int, organization_id: int):
    """Delete a failure by ID within organization"""
    result = await db.execute(
        select(Failure).where(
            Failure.id == failure_id,
            Failure.organization_id == organization_id
        )
    )
    failure = result.scalar_one_or_none()
    
    if failure is None:
        return False
    
    await db.delete(failure)
    await db.commit()
    return True