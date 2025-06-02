from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.mongodb import mongodb
from app.schemas.sensor import SensorDataIn, SensorDataOut
from bson import ObjectId

async def create_sensor(sensor_data: SensorDataIn):
    """Create a new sensor reading in MongoDB"""
    result = await mongodb.sensors.insert_one(sensor_data.dict())
    return {**sensor_data.dict(), "id": str(result.inserted_id)}

async def get_sensor(sensor_id: str):
    """Get a sensor reading by its ID"""
    sensor = await mongodb.sensors.find_one({"_id": ObjectId(sensor_id)})
    if sensor:
        # Convert MongoDB _id to str
        sensor["id"] = str(sensor.pop("_id"))
        return sensor
    return None

async def update_sensor(sensor_id: str, sensor_data: SensorDataIn):
    """Update a sensor reading by its ID"""
    result = await mongodb.sensors.update_one(
        {"_id": ObjectId(sensor_id)},
        {"$set": sensor_data.dict()}
    )
    if result.modified_count:
        return await get_sensor(sensor_id)
    return None

async def delete_sensor(sensor_id: str):
    """Delete a sensor reading by its ID"""
    result = await mongodb.sensors.delete_one({"_id": ObjectId(sensor_id)})
    return result.deleted_count > 0

async def get_sensors_by_asset(asset_id: int, skip: int = 0, limit: int = 100):
    """Get all sensor readings for a specific asset"""
    cursor = mongodb.sensors.find({"asset_id": asset_id}).skip(skip).limit(limit)
    sensors = []
    async for sensor in cursor:
        sensor["id"] = str(sensor.pop("_id"))
        sensors.append(sensor)
    return sensors