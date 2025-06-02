import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.config import settings

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def create_test_machine(create_test_user, db_session):
    from app.models.machine import Machine
    
    machine = Machine(
        name="Test Machine",
        description="Test Machine Description",
        location="Test Location",
        responsible_id=1  # Suponemos que el ID del usuario admin es 1
    )
    
    db_session.add(machine)
    await db_session.commit()
    await db_session.refresh(machine)
    
    return machine

@pytest.mark.asyncio
async def test_create_machine(create_test_user, get_token_headers):
    """Test que un supervisor puede crear una nueva máquina"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("supervisor")
        response = await ac.post(
            "/machines/",
            headers=headers,
            json={
                "name": "New Machine",
                "description": "New Machine Description",
                "location": "New Location",
                "responsible_id": 1
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Machine"
        assert data["description"] == "New Machine Description"
        assert data["location"] == "New Location"

@pytest.mark.asyncio
async def test_get_machine(create_test_machine):
    """Test que se puede obtener una máquina por su ID"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get(f"/machines/{create_test_machine.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Test Machine"
        assert data["description"] == "Test Machine Description"
        assert data["location"] == "Test Location"

@pytest.mark.asyncio
async def test_update_machine(create_test_machine, get_token_headers):
    """Test que un supervisor puede actualizar una máquina"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("supervisor")
        response = await ac.put(
            f"/machines/{create_test_machine.id}",
            headers=headers,
            json={
                "name": "Updated Machine",
                "description": "Updated Machine Description",
                "location": "Updated Location",
                "responsible_id": 2  # Suponemos que el ID del usuario supervisor es 2
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Machine"
        assert data["description"] == "Updated Machine Description"
        assert data["location"] == "Updated Location"
        assert data["responsible_id"] == 2

@pytest.mark.asyncio
async def test_delete_machine(create_test_machine, get_token_headers):
    """Test que un administrador puede eliminar una máquina"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("admin")
        response = await ac.delete(
            f"/machines/{create_test_machine.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verificamos que la máquina ha sido eliminada
        response = await ac.get(f"/machines/{create_test_machine.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_machines(create_test_machine):
    """Test que se pueden obtener todas las máquinas"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get("/machines/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1