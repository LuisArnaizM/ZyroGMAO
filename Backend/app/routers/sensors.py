from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database.postgres import get_db
from app.schemas.sensor import SensorConfigCreate, SensorConfigRead, SensorConfigUpdate
from app.controllers.sensor import (
    create_sensor_config,
    get_sensor_config,
    get_sensor_configs,
    get_sensors_by_asset,
    update_sensor_config,
    delete_sensor_config
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(tags=["Sensors"])

@router.post("/", response_model=SensorConfigRead)
async def create_new_sensor_config(
    sensor_in: SensorConfigCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    return await create_sensor_config(db=db, sensor_in=sensor_in)

@router.get("/{sensor_id}", response_model=SensorConfigRead)
async def read_sensor_config(
    sensor_id: int,
    db: AsyncSession = Depends(get_db)
):
    sensor = await get_sensor_config(db=db, sensor_id=sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor configuration not found")
    return sensor

@router.get("/", response_model=List[SensorConfigRead])
async def read_sensor_configs(
    page: int = Query(1, ge=1, description="Página actual"),
    page_size: int = Query(20, ge=1, le=100, description="Número de elementos por página"),
    search: str = Query(None, description="Término de búsqueda para filtrar sensores"),
    sensor_type: str = Query(None, description="Filtrar por tipo de sensor"),
    is_active: bool = Query(None, description="Filtrar por estado activo"),
    db: AsyncSession = Depends(get_db)
):
    return await get_sensor_configs(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        sensor_type=sensor_type,
        is_active=is_active
    )

@router.get("/asset/{asset_id}", response_model=List[SensorConfigRead])
async def read_sensors_by_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_sensors_by_asset(db=db, asset_id=asset_id)

@router.put("/{sensor_id}", response_model=SensorConfigRead)
async def update_existing_sensor_config(
    sensor_id: int,
    sensor_in: SensorConfigUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    sensor = await update_sensor_config(
        db=db,
        sensor_id=sensor_id,
        sensor_in=sensor_in,
    )
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor configuration not found")
    return sensor

@router.delete("/{sensor_id}", response_model=dict)
async def delete_existing_sensor_config(
    sensor_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    result = await delete_sensor_config(db=db, sensor_id=sensor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Sensor configuration not found")
    return {"detail": "Sensor configuration deleted successfully"}