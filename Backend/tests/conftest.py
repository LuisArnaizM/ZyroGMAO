import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.database.postgres import Base, get_db
from app.models.user import User, UserRole
from app.auth.security import create_token
from passlib.context import CryptContext
from datetime import timedelta
from app.config import settings

# Crear motor de base de datos para pruebas
engine = create_async_engine(settings.test_postgres_url)
TestingSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Cliente de MongoDB para pruebas
mongo_client = AsyncIOMotorClient(settings.test_mongodb_url)
test_mongodb = mongo_client[settings.test_mongodb_db]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Sobrescribir dependencias para usar bases de datos de prueba
async def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        await db.close()

app.dependency_overrides[get_db] = override_get_db

# Cliente de prueba para FastAPI
@pytest.fixture
def client():
    return TestClient(app)

# Fixture para crear tablas antes de los tests y eliminarlas después
@pytest.fixture(scope="function")
async def setup_database():
    # Crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Después de los tests, eliminar todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Fixture para limpiar MongoDB después de cada test
@pytest.fixture(scope="function")
async def clean_mongodb():
    yield
    # Limpiar colecciones de MongoDB después de los tests
    await test_mongodb.sensors.delete_many({})

# Fixture para crear un usuario de prueba
@pytest.fixture
async def create_test_user():
    async with TestingSessionLocal() as db:
        # Crear usuarios de prueba con diferentes roles
        admin_user = User(
            email="admin@example.com",
            hashed_password=pwd_context.hash("adminpass"),
            role=UserRole.admin
        )
        
        supervisor_user = User(
            email="supervisor@example.com",
            hashed_password=pwd_context.hash("supervisorpass"),
            role=UserRole.supervisor
        )
        
        tecnico_user = User(
            email="tecnico@example.com",
            hashed_password=pwd_context.hash("tecnicopass"),
            role=UserRole.tecnico
        )
        
        consultor_user = User(
            email="consultor@example.com",
            hashed_password=pwd_context.hash("consultorpass"),
            role=UserRole.consultor
        )
        
        db.add_all([admin_user, supervisor_user, tecnico_user, consultor_user])
        await db.commit()

# Fixture para generar tokens de autenticación
@pytest.fixture
def get_token_headers():
    def _get_token_headers(role="admin"):
        email_map = {
            "admin": "admin@example.com",
            "supervisor": "supervisor@example.com",
            "tecnico": "tecnico@example.com",
            "consultor": "consultor@example.com"
        }
        
        email = email_map.get(role, "admin@example.com")
        token, _ = create_token(
            data={"sub": email, "role": role.capitalize()},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )
        
        return {"Authorization": f"Bearer {token}"}
    
    return _get_token_headers

# Fixture para crear una sesión de base de datos
@pytest.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session

# Resolver problema con asyncio en tests
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()