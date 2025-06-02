import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.config import settings

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def create_test_asset_for_maintenance(create_test_user, db_session):
    from app.models.asset import Asset
    
    asset = Asset(
        name="Maintenance Test Asset",
        location="Maintenance Test Location",
        responsible_id=1  # Suponemos que el ID del usuario admin es 1
    )
    
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)
    
    return asset

@pytest.fixture
async def create_test_maintenance(create_test_asset_for_maintenance, db_session):
    from app.models.maintenance import Maintenance
    
    maintenance = Maintenance(
        asset_id=create_test_asset_for_maintenance.id,
        user_id=1,  # Suponemos que el ID del usuario admin es 1
        description="Test maintenance",
        status="pending"
    )
    
    db_session.add(maintenance)
    await db_session.commit()
    await db_session.refresh(maintenance)
    
    return maintenance

@pytest.mark.asyncio
async def test_create_maintenance(create_test_asset_for_maintenance, get_token_headers):
    """Test que un técnico puede crear un nuevo registro de mantenimiento"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("tecnico")
        response = await ac.post(
            "/maintenance/",
            headers=headers,
            json={
                "asset_id": create_test_asset_for_maintenance.id,
                "user_id": 3,  # Suponemos que el ID del usuario técnico es 3
                "description": "New maintenance task"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["asset_id"] == create_test_asset_for_maintenance.id
        assert data["description"] == "New maintenance task"
        assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_get_maintenance(create_test_maintenance):
    """Test que se puede obtener un registro de mantenimiento por su ID"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get(f"/maintenance/{create_test_maintenance.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == "Test maintenance"
        assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_update_maintenance(create_test_maintenance, get_token_headers):
    """Test que un técnico puede actualizar un registro de mantenimiento"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("tecnico")
        response = await ac.put(
            f"/maintenance/{create_test_maintenance.id}",
            headers=headers,
            json={
                "description": "Updated maintenance",
                "status": "completed"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == "Updated maintenance"
        assert data["status"] == "completed"

@pytest.mark.asyncio
async def test_get_maintenance_by_asset(create_test_maintenance, create_test_asset_for_maintenance):
    """Test que se pueden obtener los registros de mantenimiento por asset_id"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get(f"/maintenance/asset/{create_test_asset_for_maintenance.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["asset_id"] == create_test_asset_for_maintenance.id

@pytest.mark.asyncio
async def test_delete_maintenance(create_test_maintenance, get_token_headers):
    """Test que un supervisor puede eliminar un registro de mantenimiento"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("supervisor")
        response = await ac.delete(
            f"/maintenance/{create_test_maintenance.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verificamos que el registro ha sido eliminado
        response = await ac.get(f"/maintenance/{create_test_maintenance.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND