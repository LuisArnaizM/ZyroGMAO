import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime, timedelta

from app.main import app
from app.config import settings

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def create_test_task(create_test_user, db_session):
    from app.models.task import Task
    from app.models.machine import Machine
    
    # Crear máquina de prueba si no existe
    machine = Machine(
        name="Task Test Machine",
        description="Machine for Task Test",
        location="Test Location",
        responsible_id=1
    )
    
    db_session.add(machine)
    await db_session.commit()
    await db_session.refresh(machine)
    
    # Crear tarea de prueba
    task = Task(
        name="Test Task",
        description="Test Task Description",
        assigned_to=3,  # ID de usuario técnico
        machine_id=machine.id,
        due_date=datetime.utcnow() + timedelta(days=7),
        created_by="admin@example.com"
    )
    
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    return task

@pytest.mark.asyncio
async def test_create_task(create_test_user, get_token_headers):
    """Test que un técnico puede crear una nueva tarea"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        # Primero necesitamos obtener una máquina para asignarle la tarea
        headers = get_token_headers("supervisor")
        machine_response = await ac.post(
            "/machines/",
            headers=headers,
            json={
                "name": "Machine for Task",
                "description": "Machine Description",
                "location": "Location",
                "responsible_id": 1
            }
        )
        assert machine_response.status_code == status.HTTP_200_OK
        machine_id = machine_response.json()["id"]
        
        # Ahora creamos la tarea
        headers = get_token_headers("tecnico")
        due_date = (datetime.utcnow() + timedelta(days=5)).isoformat()
        response = await ac.post(
            "/tasks/",
            headers=headers,
            json={
                "name": "New Task",
                "description": "New Task Description",
                "assigned_to": 3,
                "machine_id": machine_id,
                "due_date": due_date
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Task"
        assert data["description"] == "New Task Description"
        assert data["machine_id"] == machine_id

@pytest.mark.asyncio
async def test_get_task(create_test_task):
    """Test que se puede obtener una tarea por su ID"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get(f"/tasks/{create_test_task.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Test Task"
        assert data["description"] == "Test Task Description"

@pytest.mark.asyncio
async def test_update_task(create_test_task, get_token_headers):
    """Test que un técnico puede actualizar una tarea"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("tecnico")
        due_date = (datetime.utcnow() + timedelta(days=3)).isoformat()
        response = await ac.put(
            f"/tasks/{create_test_task.id}",
            headers=headers,
            json={
                "name": "Updated Task",
                "description": "Updated Task Description",
                "due_date": due_date
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Task"
        assert data["description"] == "Updated Task Description"

@pytest.mark.asyncio
async def test_delete_task(create_test_task, get_token_headers):
    """Test que un supervisor puede eliminar una tarea"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("supervisor")
        response = await ac.delete(
            f"/tasks/{create_test_task.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verificamos que la tarea ha sido eliminada
        response = await ac.get(f"/tasks/{create_test_task.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_tasks(create_test_task):
    """Test que se pueden obtener todas las tareas"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get("/tasks/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1