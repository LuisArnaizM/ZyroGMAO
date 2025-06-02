import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.config import settings

pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_create_user(create_test_user, get_token_headers):
    """Test que un administrador puede crear un nuevo usuario"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("admin")
        response = await ac.post(
            "/users/",
            headers=headers,
            json={
                "email": "newuser@example.com",
                "password": "newpass",
                "role": "Tecnico"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "Tecnico"

@pytest.mark.asyncio
async def test_create_user_unauthorized(create_test_user, get_token_headers):
    """Test que un usuario no administrador no puede crear usuarios"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("tecnico")
        response = await ac.post(
            "/users/",
            headers=headers,
            json={
                "email": "newuser@example.com",
                "password": "newpass",
                "role": "Tecnico"
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_get_users(create_test_user, get_token_headers):
    """Test que un administrador puede obtener la lista de usuarios"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("admin")
        response = await ac.get("/users/", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 4  # Al menos los 4 usuarios de prueba

@pytest.mark.asyncio
async def test_get_me(create_test_user, get_token_headers):
    """Test que un usuario autenticado puede obtener su información"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("admin")
        response = await ac.get("/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "admin@example.com"
        assert data["role"] == "Admin"

@pytest.mark.asyncio
async def test_update_user(create_test_user, get_token_headers, db_session):
    """Test que un administrador puede actualizar un usuario"""
    # Primero obtenemos la lista de usuarios para encontrar el ID
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("admin")
        response = await ac.get("/users/", headers=headers)
        users = response.json()
        
        # Buscar el usuario consultor
        consultor = next((u for u in users if u["email"] == "consultor@example.com"), None)
        assert consultor is not None
        
        # Ahora actualizamos el usuario
        user_id = consultor["id"]
        response = await ac.put(
            f"/users/{user_id}",
            headers=headers,
            json={
                "email": "consultor_updated@example.com",
                "role": "Tecnico"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "consultor_updated@example.com"
        assert data["role"] == "Tecnico"

@pytest.mark.asyncio
async def test_delete_user(create_test_user, get_token_headers):
    """Test que un administrador puede eliminar un usuario"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        # Primero creamos un usuario para eliminarlo
        headers = get_token_headers("admin")
        create_response = await ac.post(
            "/users/",
            headers=headers,
            json={
                "email": "to_delete@example.com",
                "password": "deletepass",
                "role": "Consultor"
            }
        )
        assert create_response.status_code == status.HTTP_200_OK
        created_user = create_response.json()
        
        # Obtener todos los usuarios para encontrar el ID
        get_response = await ac.get("/users/", headers=headers)
        users = get_response.json()
        user_to_delete = next((u for u in users if u["email"] == "to_delete@example.com"), None)
        assert user_to_delete is not None
        
        # Ahora eliminamos el usuario
        user_id = user_to_delete["id"]
        response = await ac.delete(f"/users/{user_id}", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verificamos que el usuario ha sido eliminado
        check_response = await ac.get(f"/users/{user_id}", headers=headers)
        assert check_response.status_code == status.HTTP_404_NOT_FOUND