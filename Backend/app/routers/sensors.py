from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from app.database.postgres import get_db
from app.schemas.sensor import (
    SensorConfigCreate,
    SensorConfigRead,
    SensorConfigUpdate,
    SensorReadingCreate,
    SensorReadingRead
)
from app.controllers.sensor import (
    # Configuración de sensores (PostgreSQL)
    create_sensor_config,
    get_sensor_config,
    get_sensors_by_asset_config,
    update_sensor_config,
    delete_sensor_config,
    # Lecturas de sensores (MongoDB)
    create_sensor_reading,
    get_sensor_reading,
    get_readings_by_sensor,
    get_latest_readings_by_asset
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/sensors", tags=["Sensors"])

# Rutas para la configuración de sensores (PostgreSQL)
@router.post("/config", response_model=SensorConfigRead)
async def create_new_sensor_config(
    sensor_config: SensorConfigCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    """Crear una nueva configuración de sensor"""
    return await create_sensor_config(db=db, sensor_config=sensor_config)

@router.get("/config/{sensor_id}", response_model=SensorConfigRead)
async def read_sensor_config(
    sensor_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Obtener la configuración de un sensor por ID"""
    sensor = await get_sensor_config(db=db, sensor_id=sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor configuration not found")
    return sensor

@router.get("/config/asset/{asset_id}", response_model=List[SensorConfigRead])
async def read_sensors_by_asset_config(
    asset_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Obtener todas las configuraciones de sensores para un activo"""
    return await get_sensors_by_asset_config(
        db=db, 
        asset_id=asset_id,
        page=page,
        page_size=page_size
    )

@router.put("/config/{sensor_id}", response_model=SensorConfigRead)
async def update_sensor_config_endpoint(
    sensor_id: int,
    sensor_update: SensorConfigUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    """Actualizar la configuración de un sensor"""
    sensor = await update_sensor_config(db=db, sensor_id=sensor_id, sensor_config=sensor_update)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor configuration not found")
    return sensor

@router.delete("/config/{sensor_id}", response_model=dict)
async def delete_sensor_config_endpoint(
    sensor_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin"]))
):
    """Eliminar la configuración de un sensor"""
    result = await delete_sensor_config(db=db, sensor_id=sensor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Sensor configuration not found")
    return {"detail": "Sensor configuration deleted successfully"}

# Rutas para las lecturas de sensores (MongoDB)
@router.post("/readings", response_model=SensorReadingRead)
async def create_new_sensor_reading(
    reading: SensorReadingCreate,
    user = Depends(get_current_user)
):
    """Crear una nueva lectura de sensor"""
    return await create_sensor_reading(reading=reading)

@router.get("/readings/{reading_id}", response_model=SensorReadingRead)
async def read_sensor_reading(reading_id: str):
    """Obtener una lectura de sensor por ID"""
    reading = await get_sensor_reading(reading_id=reading_id)
    if not reading:
        raise HTTPException(status_code=404, detail="Sensor reading not found")
    return reading

@router.get("/readings/sensor/{sensor_id}", response_model=List[SensorReadingRead])
async def read_readings_by_sensor_endpoint(
    sensor_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Obtener todas las lecturas de un sensor específico"""
    return await get_readings_by_sensor(
        sensor_id=sensor_id,
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/readings/asset/{asset_id}/latest", response_model=List[SensorReadingRead])
async def read_latest_readings_by_asset_endpoint(
    asset_id: int,
    limit: int = Query(10, ge=1, le=100)
):
    """Obtener las últimas lecturas de todos los sensores para un activo"""
    return await get_latest_readings_by_asset(asset_id=asset_id, limit=limit)