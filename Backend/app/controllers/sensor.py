from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.mongodb import mongodb
from app.models.sensor import Sensor
from app.schemas.sensor import (
    SensorConfigCreate, 
    SensorConfigRead, 
    SensorConfigUpdate,
    SensorReadingCreate, 
    SensorReadingRead
)
from bson import ObjectId
from datetime import datetime
from typing import List

# Funciones para la configuración de sensores (PostgreSQL)
async def create_sensor_config(db: AsyncSession, sensor_config: SensorConfigCreate):
    """Crear un nuevo sensor en PostgreSQL"""
    new_sensor = Sensor(**sensor_config.model_dump())
    db.add(new_sensor)
    await db.commit()
    await db.refresh(new_sensor)
    return new_sensor

async def get_sensor_config(db: AsyncSession, sensor_id: int):
    """Obtener la configuración de un sensor por ID desde PostgreSQL"""
    result = await db.execute(select(Sensor).where(Sensor.id == sensor_id))
    return result.scalar_one_or_none()

async def get_sensors_by_asset_config(
    db: AsyncSession,
    asset_id: int,
    page: int = 1,
    page_size: int = 20
):
    """Obtener todos los sensores de un activo desde PostgreSQL"""
    offset = (page - 1) * page_size
    query = select(Sensor).where(Sensor.asset_id == asset_id).offset(offset).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()

async def update_sensor_config(db: AsyncSession, sensor_id: int, sensor_config: SensorConfigUpdate):
    """Actualizar la configuración de un sensor en PostgreSQL"""
    result = await db.execute(select(Sensor).where(Sensor.id == sensor_id))
    sensor = result.scalar_one_or_none()
    
    if not sensor:
        return None
    
    for key, value in sensor_config.model_dump(exclude_unset=True).items():
        setattr(sensor, key, value)
    
    await db.commit()
    await db.refresh(sensor)
    return sensor

async def delete_sensor_config(db: AsyncSession, sensor_id: int):
    """Eliminar la configuración de un sensor en PostgreSQL"""
    result = await db.execute(select(Sensor).where(Sensor.id == sensor_id))
    sensor = result.scalar_one_or_none()
    
    if not sensor:
        return False
    
    await db.delete(sensor)
    await db.commit()
    return True

# Funciones para las lecturas de sensores (MongoDB)
async def create_sensor_reading(reading: SensorReadingCreate):
    """Crear una nueva lectura de sensor en MongoDB"""
    result = await mongodb.sensor_readings.insert_one(reading.model_dump())
    return {**reading.model_dump(), "id": str(result.inserted_id)}

async def get_sensor_reading(reading_id: str):
    """Obtener una lectura de sensor por ID desde MongoDB"""
    reading = await mongodb.sensor_readings.find_one({"_id": ObjectId(reading_id)})
    if reading:
        reading["id"] = str(reading.pop("_id"))
        return reading
    return None

async def get_readings_by_sensor(
    sensor_id: int,
    page: int = 1,
    page_size: int = 20,
    start_date: datetime = None,
    end_date: datetime = None
):
    """
    Obtener todas las lecturas de un sensor específico desde MongoDB
    
    Parameters:
    - sensor_id: ID del sensor en PostgreSQL
    - page: Número de página (comienza desde 1)
    - page_size: Número de registros por página
    - start_date: Fecha inicial para filtrar (opcional)
    - end_date: Fecha final para filtrar (opcional)
    """
    skip = (page - 1) * page_size
    
    # Crear filtro base
    filter_query = {"sensor_id": sensor_id}
    
    # Añadir filtro de fecha si es necesario
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        filter_query["timestamp"] = date_filter
    
    # Ejecutar consulta
    cursor = mongodb.sensor_readings.find(filter_query).sort("timestamp", -1).skip(skip).limit(page_size)
    readings = await cursor.to_list(length=page_size)
    
    # Convertir ObjectId a string
    for reading in readings:
        reading["id"] = str(reading.pop("_id"))
    
    return readings

async def get_latest_readings_by_asset(asset_id: int, limit: int = 10):
    """Obtener las últimas lecturas de todos los sensores de un activo desde MongoDB"""
    pipeline = [
        {"$match": {"asset_id": asset_id}},
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$sensor_id",
            "last_reading": {"$first": "$$ROOT"}
        }},
        {"$replaceRoot": {"newRoot": "$last_reading"}},
        {"$limit": limit}
    ]
    
    cursor = mongodb.sensor_readings.aggregate(pipeline)
    readings = await cursor.to_list(length=limit)
    
    # Convertir ObjectId a string
    for reading in readings:
        reading["id"] = str(reading.pop("_id"))
    
    return readings

# Mantener función existente para compatibilidad
async def save_sensor_reading(sensor_id: int, asset_id: int, value: float):
    """Guarda una lectura de sensor en MongoDB"""
    data = {
        "sensor_id": sensor_id,
        "asset_id": asset_id,
        "value": value,
        "timestamp": datetime.now()
    }
    await mongodb.sensor_readings.insert_one(data)