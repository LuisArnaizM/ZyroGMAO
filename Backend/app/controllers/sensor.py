from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.sensor import Sensor
from app.models.asset import Asset
from app.schemas.sensor import SensorConfigCreate, SensorConfigRead, SensorConfigUpdate
from datetime import datetime

async def create_sensor_config(db: AsyncSession, sensor_in: SensorConfigCreate, organization_id: int):
    """Create a new sensor configuration"""
    
    # Verificar que el asset existe en la organización
    asset = await db.execute(
        select(Asset).where(
            Asset.id == sensor_in.asset_id,
            Asset.organization_id == organization_id
        )
    )
    if not asset.scalar_one_or_none():
        raise ValueError(f"Asset with ID {sensor_in.asset_id} does not exist in this organization")
    
    sensor_data = sensor_in.model_dump()
    sensor_data['organization_id'] = organization_id
    
    new_sensor = Sensor(**sensor_data)
    db.add(new_sensor)
    await db.commit()
    await db.refresh(new_sensor)
    return new_sensor

async def get_sensor_config(db: AsyncSession, sensor_id: int, organization_id: int):
    """Get a sensor configuration by ID within organization"""
    result = await db.execute(
        select(Sensor).where(
            Sensor.id == sensor_id,
            Sensor.organization_id == organization_id
        )
    )
    return result.scalar_one_or_none()

async def get_sensor_configs(
    db: AsyncSession,
    organization_id: int,
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    sensor_type: str = None,
    is_active: bool = None
):
    """Get all sensor configurations with filters, pagination and search capability within organization"""
    offset = (page - 1) * page_size
    
    query = select(Sensor).where(Sensor.organization_id == organization_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Sensor.name.ilike(search_term)) |
            (Sensor.description.ilike(search_term)) |
            (Sensor.location.ilike(search_term))
        )
    
    if sensor_type:
        query = query.where(Sensor.sensor_type == sensor_type)
    
    if is_active is not None:
        query = query.where(Sensor.is_active == is_active)
    
    query = query.offset(offset).limit(page_size).order_by(Sensor.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def get_sensors_by_asset(db: AsyncSession, asset_id: int, organization_id: int):
    """Get all sensor configurations for a specific asset within organization"""
    result = await db.execute(
        select(Sensor).where(
            Sensor.asset_id == asset_id,
            Sensor.organization_id == organization_id
        ).order_by(Sensor.name.asc())
    )
    return result.scalars().all()

async def update_sensor_config(db: AsyncSession, sensor_id: int, sensor_in: SensorConfigUpdate, organization_id: int):
    """Update a sensor configuration by ID within organization"""
    result = await db.execute(
        select(Sensor).where(
            Sensor.id == sensor_id,
            Sensor.organization_id == organization_id
        )
    )
    sensor = result.scalar_one_or_none()
    
    if sensor is None:
        return None
    
    update_data = sensor_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sensor, key, value)
    
    sensor.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(sensor)
    return sensor

async def delete_sensor_config(db: AsyncSession, sensor_id: int, organization_id: int):
    """Delete a sensor configuration by ID within organization"""
    result = await db.execute(
        select(Sensor).where(
            Sensor.id == sensor_id,
            Sensor.organization_id == organization_id
        )
    )
    sensor = result.scalar_one_or_none()
    
    if sensor is None:
        return False
    
    await db.delete(sensor)
    await db.commit()
    return True