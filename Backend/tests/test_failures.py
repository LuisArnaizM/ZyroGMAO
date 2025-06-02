import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.config import settings

pytestmark = pytest.mark.asyncio

# Fixture para crear un activo para las pruebas
@pytest.fixture
async def create_test_asset_for_failure(create_test_user, db_session):
    from app.models.asset import Asset
    
    asset = Asset(
        name="Failure Test Asset",
        location="Failure Test Location",
        responsible_id=1  # Suponemos que el ID del usuario admin es 1
    )
    
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)
    
    return asset

# Fixture para crear una solicitud de mantenimiento por fallo
@pytest.fixture
async def create_test_failure(create_test_asset_for_failure, db_session):
    from app.models.failure import MaintenanceRequest
    
    failure = MaintenanceRequest(
        asset_id=create_test_asset_for_failure.id,
        description="Test failure report",
        status="open"
    )
    
    db_session.add(failure)
    await db_session.commit()
    await db_session.refresh(failure)
    
    return failure

@pytest.mark.asyncio
async def test_create_failure(create_test_asset_for_failure, get_token_headers):
    """Test que un usuario puede crear un reporte de fallo"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("tecnico")
        response = await ac.post(
            "/failures/",
            headers=headers,
            json={
                "asset_id": create_test_asset_for_failure.id,
                "description": "New failure detected"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["asset_id"] == create_test_asset_for_failure.id
        assert data["description"] == "New failure detected"
        assert data["status"] == "open"

@pytest.mark.asyncio
async def test_get_failure(create_test_failure):
    """Test que se puede obtener un reporte de fallo por su ID"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get(f"/failures/{create_test_failure.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == "Test failure report"
        assert data["status"] == "open"

@pytest.mark.asyncio
async def test_update_failure_status(create_test_failure, get_token_headers):
    """Test que un técnico puede actualizar el estado de un fallo"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("tecnico")
        response = await ac.put(
            f"/failures/{create_test_failure.id}",
            headers=headers,
            json={
                "description": "Updated failure description",
                "status": "in_progress"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == "Updated failure description"
        assert data["status"] == "in_progress"

@pytest.mark.asyncio
async def test_get_all_failures(create_test_failure):
    """Test que se pueden obtener todos los fallos"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get("/failures/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1  # Al menos debe estar el fallo que creamos

@pytest.mark.asyncio
async def test_delete_failure(create_test_failure, get_token_headers):
    """Test que un supervisor puede eliminar un reporte de fallo"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("supervisor")
        response = await ac.delete(
            f"/failures/{create_test_failure.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verificamos que el fallo ha sido eliminado
        response = await ac.get(f"/failures/{create_test_failure.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_unauthorized_delete_failure(create_test_failure, get_token_headers):
    """Test que un consultor no puede eliminar un reporte de fallo"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("consultor")
        response = await ac.delete(
            f"/failures/{create_test_failure.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN