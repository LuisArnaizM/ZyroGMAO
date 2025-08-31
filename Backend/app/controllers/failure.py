from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.failure import Failure
from app.models.asset import Asset
from app.models.component import Component
from app.schemas.failure import FailureCreate, FailureRead, FailureUpdate
from datetime import datetime, timezone
import enum as _py_enum
from app.models.enums import FailureStatus, FailureSeverity
from sqlalchemy.orm import selectinload

async def create_failure(db: AsyncSession, failure_in: FailureCreate, reported_by: int):
    """Create a new failure report"""
    
    # Validar que al menos uno de los IDs esté presente
    if not failure_in.asset_id and not failure_in.component_id:
        raise ValueError("Debe proporcionar asset_id o component_id")

    # Verificar que el asset o component existe
    if failure_in.asset_id:
        asset = await db.execute(
            select(Asset).where(
                Asset.id == failure_in.asset_id
            )
        )
        if not asset.scalar_one_or_none():
            raise ValueError(f"Asset with ID {failure_in.asset_id} does not exist")

    if failure_in.component_id:
        component = await db.execute(
            select(Component).where(
                Component.id == failure_in.component_id
            )
        )
        if not component.scalar_one_or_none():
            raise ValueError(f"Component with ID {failure_in.component_id} does not exist")
    
    failure_data = failure_in.model_dump(exclude_none=True)
    failure_data['reported_by'] = reported_by
    # Ensure status and severity are stored as the enum value strings expected by the DB
    failure_data['status'] = FailureStatus.REPORTED.value

    sev = failure_data.get('severity')
    if sev is not None:
        if isinstance(sev, _py_enum.Enum):
            failure_data['severity'] = sev.value
        else:
            failure_data['severity'] = str(sev).upper()

    new_failure = Failure(**failure_data)
    db.add(new_failure)
    await db.commit()
    await db.refresh(new_failure)
    return new_failure

async def get_failure(db: AsyncSession, failure_id: int):
    """Get a failure by ID within organization"""
    result = await db.execute(
    select(Failure).where(Failure.id == failure_id)
    )
    return result.scalar_one_or_none()

async def get_failures(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    status: str = None,
    severity: str = None
):
    """Get all failures with filters, pagination and search capability"""
    offset = (page - 1) * page_size
    
    query = select(Failure)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Failure.description.ilike(search_term)) |
            (Failure.resolution_notes.ilike(search_term))
        )
    
    if status:
        # normalize incoming filter to enum value
        if isinstance(status, _py_enum.Enum):
            status_val = status.value
        else:
            status_val = str(status).upper()
        query = query.where(Failure.status == status_val)

    if severity:
        if isinstance(severity, _py_enum.Enum):
            severity_val = severity.value
        else:
            severity_val = str(severity).upper()
        query = query.where(Failure.severity == severity_val)
    
    query = query.offset(offset).limit(page_size).order_by(Failure.reported_date.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def get_failures_with_workorder_ids(db: AsyncSession):
    """Get all failures with their associated workorder IDs"""
    result = await db.execute(
        select(Failure).options(selectinload(Failure.workorders))
    )
    failures = result.scalars().all()
    
    # Transform to include workorder_id for each failure
    failures_with_wo = []
    for failure in failures:
        # Obtener el workorder más reciente si existe
        most_recent_wo = None
        if failure.workorders:
            # Ordenar por ID (el más alto será el más reciente)
            sorted_workorders = sorted(failure.workorders, key=lambda wo: wo.id, reverse=True)
            most_recent_wo = sorted_workorders[0]
        
        failure_dict = {
            "id": failure.id,
            "description": failure.description,
            "severity": failure.severity,
            "status": failure.status,
            "reported_by": failure.reported_by,
            "reported_date": failure.reported_date,
            "resolved_date": failure.resolved_date,
            "asset_id": failure.asset_id,
            "component_id": failure.component_id,
            "created_at": failure.created_at,
            "updated_at": failure.updated_at,
            # Tomar solo el workorder más reciente o None
            "workorder_id": most_recent_wo.id if most_recent_wo else None
        }
        failures_with_wo.append(failure_dict)
    
    return failures_with_wo
async def get_failures_by_asset(db: AsyncSession, asset_id: int):
    """Get all failures for a specific asset"""
    result = await db.execute(
        select(Failure).where(Failure.asset_id == asset_id).order_by(Failure.reported_date.desc())
    )
    return result.scalars().all()

async def update_failure(db: AsyncSession, failure_id: int, failure_in: FailureUpdate):
    """Update a failure by ID"""
    result = await db.execute(
        select(Failure).where(Failure.id == failure_id)
    )
    failure = result.scalar_one_or_none()
    
    if failure is None:
        return None
    
    update_data = failure_in.model_dump(exclude_unset=True)
    
    # Si se marca como resuelto y no tenía fecha de resolución, agregarla
    status_in = update_data.get('status')
    if status_in is not None:
        if isinstance(status_in, _py_enum.Enum):
            status_norm = status_in.value
        else:
            status_norm = str(status_in).upper()
        update_data['status'] = status_norm
        if status_norm == FailureStatus.RESOLVED.value and not failure.resolved_date:
            update_data['resolved_date'] = datetime.now(timezone.utc)

    # Normalize severity if present
    sev_in = update_data.get('severity')
    if sev_in is not None:
        if isinstance(sev_in, _py_enum.Enum):
            update_data['severity'] = sev_in.value
        else:
            update_data['severity'] = str(sev_in).upper()

    for key, value in update_data.items():
        setattr(failure, key, value)
    
    failure.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(failure)
    return failure

async def delete_failure(db: AsyncSession, failure_id: int):
    """Delete a failure by ID"""
    result = await db.execute(
        select(Failure).where(Failure.id == failure_id)
    )
    failure = result.scalar_one_or_none()
    
    if failure is None:
        return False
    
    await db.delete(failure)
    await db.commit()
    return True