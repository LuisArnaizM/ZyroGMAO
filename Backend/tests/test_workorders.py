import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.config import settings

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def create_test_prerequisites(create_test_user, db_session):
    """Crear los requisitos previos para las órdenes de trabajo: tarea y solicitud de mantenimiento"""
    from app.models.task import Task
    from app.models.failure import MaintenanceRequest
    from app.models.asset import Asset
    from app.models.machine import Machine
    from datetime import datetime, timedelta
    
    # Crear activo
    asset = Asset(
        name="WorkOrder Test Asset",
        location="WorkOrder Test Location",
        responsible_id=1
    )
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)
    
    # Crear máquina
    machine = Machine(
        name="WorkOrder Test Machine",
        description="Machine for WorkOrder Test",
        location="Test Location",
        responsible_id=1
    )
    db_session.add(machine)
    await db_session.commit()
    await db_session.refresh(machine)
    
    # Crear solicitud de mantenimiento
    maintenance_request = MaintenanceRequest(
        asset_id=asset.id,
        description="WorkOrder Test Maintenance Request",
        status="open"
    )
    db_session.add(maintenance_request)
    await db_session.commit()
    await db_session.refresh(maintenance_request)
    
    # Crear tarea
    task = Task(
        name="WorkOrder Test Task",
        description="Task for WorkOrder Test",
        assigned_to=3,  # ID de usuario técnico
        machine_id=machine.id,
        due_date=datetime.utcnow() + timedelta(days=7),
        created_by="admin@example.com"
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    return {"task": task, "maintenance_request": maintenance_request}

@pytest.fixture
async def create_test_workorder(create_test_prerequisites, db_session):
    from app.models.workorder import WorkOrder
    
    workorder = WorkOrder(
        task_id=create_test_prerequisites["task"].id,
        maintenance_id=create_test_prerequisites["maintenance_request"].id,
        status="pending",
        created_by="admin@example.com"
    )
    
    db_session.add(workorder)
    await db_session.commit()
    await db_session.refresh(workorder)
    
    return workorder

@pytest.mark.asyncio
async def test_create_workorder(create_test_prerequisites, get_token_headers):
    """Test que un técnico puede crear una nueva orden de trabajo"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("tecnico")
        response = await ac.post(
            "/workorders/",
            headers=headers,
            json={
                "task_id": create_test_prerequisites["task"].id,
                "maintenance_id": create_test_prerequisites["maintenance_request"].id,
                "description": "New WorkOrder Description",
                "status": "pending"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["task_id"] == create_test_prerequisites["task"].id
        assert data["maintenance_id"] == create_test_prerequisites["maintenance_request"].id
        assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_get_workorder(create_test_workorder):
    """Test que se puede obtener una orden de trabajo por su ID"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get(f"/workorders/{create_test_workorder.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["task_id"] == create_test_workorder.task_id
        assert data["maintenance_id"] == create_test_workorder.maintenance_id
        assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_update_workorder(create_test_workorder, get_token_headers):
    """Test que un técnico puede actualizar una orden de trabajo"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("tecnico")
        response = await ac.put(
            f"/workorders/{create_test_workorder.id}",
            headers=headers,
            json={
                "status": "in_progress",
                "description": "Updated WorkOrder Description"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["description"] == "Updated WorkOrder Description"

@pytest.mark.asyncio
async def test_get_workorders_by_maintenance(create_test_workorder, create_test_prerequisites):
    """Test que se pueden obtener las órdenes de trabajo de una solicitud de mantenimiento"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.get(f"/workorders/maintenance/{create_test_prerequisites['maintenance_request'].id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert data[0]["maintenance_id"] == create_test_prerequisites["maintenance_request"].id

@pytest.mark.asyncio
async def test_delete_workorder(create_test_workorder, get_token_headers):
    """Test que un supervisor puede eliminar una orden de trabajo"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("supervisor")
        response = await ac.delete(
            f"/workorders/{create_test_workorder.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verificamos que la orden de trabajo ha sido eliminada
        response = await ac.get(f"/workorders/{create_test_workorder.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND