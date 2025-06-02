import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.config import settings

pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_login_success(create_test_user):
    """Test que un usuario puede iniciar sesión correctamente"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.post(
            "/auth/token",
            data={
                "username": "admin@example.com",
                "password": "adminpass"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Test que un usuario no puede iniciar sesión con credenciales incorrectas"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.post(
            "/auth/token",
            data={
                "username": "admin@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_register_new_user(setup_database):
    """Test que un nuevo usuario puede registrarse"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "newuserpass",
                "role": "Tecnico"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "Tecnico"

@pytest.mark.asyncio
async def test_register_existing_email(create_test_user):
    """Test que no se puede registrar un usuario con un email ya existente"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        response = await ac.post(
            "/auth/register",
            json={
                "email": "admin@example.com",
                "password": "somepass",
                "role": "Tecnico"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_get_me(create_test_user, get_token_headers):
    """Test que un usuario autenticado puede obtener su información"""
    async with AsyncClient(app=app, base_url=f"http://{settings.host}:{settings.port}") as ac:
        headers = get_token_headers("admin")
        response = await ac.get("/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "admin@example.com"
        assert data["role"] == "Admin"