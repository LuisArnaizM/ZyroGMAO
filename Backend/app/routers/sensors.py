from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from app.schemas.sensor import SensorDataIn, SensorDataOut
from app.crud.sensor import (
    create_sensor, 
    get_sensor, 
    update_sensor, 
    delete_sensor,
    get_sensors_by_asset
)
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/sensors", tags=["Sensors"])

@router.post("/", response_model=SensorDataOut)
async def create_sensor_endpoint(sensor_data: SensorDataIn):
    return await create_sensor(sensor_data=sensor_data)

@router.get("/{sensor_id}", response_model=SensorDataOut)
async def read_sensor(sensor_id: str):
    sensor = await get_sensor(sensor_id=sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor

@router.put("/{sensor_id}", response_model=SensorDataOut)
async def update_sensor_endpoint(sensor_id: str, sensor_data: SensorDataIn):
    sensor = await update_sensor(sensor_id=sensor_id, sensor_data=sensor_data)
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor

@router.delete("/{sensor_id}", response_model=dict)
async def delete_sensor_endpoint(sensor_id: str):
    result = await delete_sensor(sensor_id=sensor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return {"detail": "Sensor deleted successfully"}

@router.get("/asset/{asset_id}", response_model=List[SensorDataOut])
async def read_sensors_by_asset(
    asset_id: int, 
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000)
):
    return await get_sensors_by_asset(asset_id=asset_id, skip=skip, limit=limit)