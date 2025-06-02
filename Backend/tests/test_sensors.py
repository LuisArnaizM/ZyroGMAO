import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime

from app.main import app
from app.config import settings
from app.database.mongodb import mongodb

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def create_test_sensor():
    data = {
        "asset_id": 1,
        "sensor_type": "temperature",
        "value": 25.5,
        "timestamp": datetime.utcnow()
    }
    
    result = await mongodb.sensors.insert_one(data)
    data["id"] = str(result.inserted_id)
    return data

@pytest.mark.asyncio
async def test_create_sensor(clean_mongodb):
    """Test que se puede crear un nuevo sensor"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.post(
            "/sensors/",
            json={
                "asset_id": 1,
                "sensor_type": "temperature",
                "value": 25.5,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["asset_id"] == 1
        assert data["sensor_type"] == "temperature"
        assert data["value"] == 25.5
        assert "id" in data

@pytest.mark.asyncio
async def test_get_sensor(create_test_sensor):
    """Test que se puede obtener un sensor por su ID"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get(f"/sensors/{create_test_sensor['id']}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["asset_id"] == create_test_sensor["asset_id"]
        assert data["sensor_type"] == create_test_sensor["sensor_type"]
        assert data["value"] == create_test_sensor["value"]

@pytest.mark.asyncio
async def test_update_sensor(create_test_sensor):
    """Test que se puede actualizar un sensor"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.put(
            f"/sensors/{create_test_sensor['id']}",
            json={
                "asset_id": 1,
                "sensor_type": "humidity",
                "value": 60.0,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["asset_id"] == 1
        assert data["sensor_type"] == "humidity"
        assert data["value"] == 60.0

@pytest.mark.asyncio
async def test_delete_sensor(create_test_sensor):
    """Test que se puede eliminar un sensor"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.delete(f"/sensors/{create_test_sensor['id']}")
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verificamos que el sensor ha sido eliminado
        response = await ac.get(f"/sensors/{create_test_sensor['id']}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_sensors_by_asset(clean_mongodb):
    """Test que se pueden obtener sensores por asset_id"""
    # Crear varios sensores para un activo
    sensors_data = [
        {
            "asset_id": 1,
            "sensor_type": "temperature",
            "value": 25.5,
            "timestamp": datetime.utcnow()
        },
        {
            "asset_id": 1,
            "sensor_type": "humidity",
            "value": 60.0,
            "timestamp": datetime.utcnow()
        },
        {
            "asset_id": 2,  # Este es de otro activo
            "sensor_type": "pressure",
            "value": 1013.0,
            "timestamp": datetime.utcnow()
        }
    ]
    
    await mongodb.sensors.insert_many(sensors_data)
    
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get("/sensors/asset/1")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2  # Solo los sensores del activo 1