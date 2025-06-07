from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.config import get_database_url
from typing import AsyncGenerator
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base para los modelos
Base = declarative_base()

# Engine de la base de datos
engine = create_async_engine(
    get_database_url(),
    echo=True,  # Para desarrollo, cambiar a False en producción
    pool_pre_ping=True,
    pool_recycle=300,
)

# Session maker
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generador de sesiones de base de datos para dependency injection.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

async def create_tables():
    """
    Crea todas las tablas definidas en los modelos.
    """
    try:
        # Importar todos los modelos para que se registren con Base
        from app.models import user, organization, asset, sensor, failure, maintenance, task, workorder, sensordata
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Tablas creadas exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {e}")
        raise e

async def drop_tables():
    """
    Elimina todas las tablas de la base de datos.
    """
    try:
        # Importar todos los modelos para que se registren con Base
        from app.models import user, organization, asset, sensor, failure, maintenance, task, workorder, sensordata
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("✅ Tablas eliminadas exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error eliminando tablas: {e}")
        raise e

async def check_connection():
    """
    Verifica la conexión a la base de datos.
    """
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"❌ Error de conexión a la base de datos: {e}")
        return False