import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.config import settings

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def create_test_asset(create_test_user, db_session):
    from app.models.asset import Asset
    
    asset = Asset(
        name="Test Asset",
        location="Test Location",
        responsible_id=1  # Suponemos que el ID del usuario admin es 1
    )
    
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)
    
    return asset

@pytest.mark.asyncio
async def test_create_asset(create_test_user, get_token_headers):
    """Test que un supervisor puede crear un nuevo activo"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("supervisor")
        response = await ac.post(
            "/assets/",
            headers=headers,
            json={
                "name": "New Asset",
                "location": "Location A",
                "responsible_id": 1  # Suponemos que el ID del usuario admin es 1
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Asset"
        assert data["location"] == "Location A"

@pytest.mark.asyncio
async def test_get_asset(create_test_asset):
    """Test que se puede obtener un activo por su ID"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get(f"/assets/{create_test_asset.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Test Asset"
        assert data["location"] == "Test Location"

@pytest.mark.asyncio
async def test_update_asset(create_test_asset, get_token_headers):
    """Test que un supervisor puede actualizar un activo"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("supervisor")
        response = await ac.put(
            f"/assets/{create_test_asset.id}",
            headers=headers,
            json={
                "name": "Updated Asset",
                "location": "Updated Location",
                "responsible_id": 2  # Suponemos que el ID del usuario supervisor es 2
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Asset"
        assert data["location"] == "Updated Location"
        assert data["responsible_id"] == 2

@pytest.mark.asyncio
async def test_delete_asset(create_test_asset, get_token_headers):
    """Test que un administrador puede eliminar un activo"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("admin")
        response = await ac.delete(
            f"/assets/{create_test_asset.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verificamos que el activo ha sido eliminado
        response = await ac.get(f"/assets/{create_test_asset.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_assets(create_test_asset):
    """Test que se pueden obtener todos los activos"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get("/assets/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1