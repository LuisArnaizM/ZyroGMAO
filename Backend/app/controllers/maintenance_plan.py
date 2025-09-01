from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.maintenancePlan import MaintenancePlan
from app.schemas.maintenance_plan import (
    MaintenancePlanCreate,
    MaintenancePlanRead,
    MaintenancePlanUpdate,
)
from datetime import datetime, timezone


def _naive_utc(dt: datetime | None) -> datetime | None:
    """Convierte cualquier datetime a naive UTC (sin tzinfo) para columnas TIMESTAMP WITHOUT TIME ZONE.
    - Si viene None -> None
    - Si viene con tz -> se convierte a UTC y se quita tzinfo
    - Si viene naive -> se asume ya en UTC y se deja igual
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


async def create_maintenance_plan(db: AsyncSession, plan_in: MaintenancePlanCreate):
    # Normalizar fechas para evitar mezcla aware/naive (start/next/last son columnas sin timezone)
    start_date = _naive_utc(plan_in.start_date) or datetime.utcnow()
    next_due_date = _naive_utc(plan_in.next_due_date)
    last_exec = _naive_utc(plan_in.last_execution_date)

    now_aware = datetime.now(timezone.utc)  # created_at / updated_at (columnas con timezone=True)

    new_plan = MaintenancePlan(
        name=plan_in.name,
        description=plan_in.description,
        plan_type=plan_in.plan_type.value if plan_in.plan_type else None,
        frequency_days=plan_in.frequency_days,
        frequency_weeks=plan_in.frequency_weeks,
        frequency_months=plan_in.frequency_months,
        estimated_duration=plan_in.estimated_duration,
        estimated_cost=plan_in.estimated_cost,
        start_date=start_date,
        next_due_date=next_due_date,
        last_execution_date=last_exec,
        active=plan_in.active,
        asset_id=plan_in.asset_id,
        component_id=plan_in.component_id,
        created_at=now_aware,
        updated_at=now_aware,
    )
    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)
    return new_plan


async def get_maintenance_plan(db: AsyncSession, plan_id: int):
    result = await db.execute(select(MaintenancePlan).where(MaintenancePlan.id == plan_id))
    return result.scalar_one_or_none()


async def get_all_maintenance_plans(db: AsyncSession, page: int = 1, page_size: int = 20, search: str = None, asset_id: int = None):
    offset = (page - 1) * page_size
    query = select(MaintenancePlan)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (MaintenancePlan.name.ilike(search_term)) |
            (MaintenancePlan.description.ilike(search_term))
        )
    if asset_id is not None:
        query = query.where(MaintenancePlan.asset_id == asset_id)
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()


async def update_maintenance_plan(db: AsyncSession, plan_id: int, plan_in: MaintenancePlanUpdate):
    result = await db.execute(select(MaintenancePlan).where(MaintenancePlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if plan is None:
        return None
    update_data = plan_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == 'plan_type' and value is not None:
            # Convert enum to string value
            setattr(plan, key, value.value if hasattr(value, 'value') else value)
        elif key in {"start_date", "next_due_date", "last_execution_date"}:
            setattr(plan, key, _naive_utc(value))
        else:
            setattr(plan, key, value)
    plan.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(plan)
    return plan


async def delete_maintenance_plan(db: AsyncSession, plan_id: int):
    result = await db.execute(select(MaintenancePlan).where(MaintenancePlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if plan is None:
        return False
    await db.delete(plan)
    await db.commit()
    return True
