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
        from app.models import user, asset, failure, maintenance, task, workorder, department, calendar
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Tablas creadas exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {e}")
        raise e

async def apply_simple_migrations():
    """
    Aplica migraciones simples idempotentes mediante ALTER TABLE IF NOT EXISTS.
    Útil para alinear el esquema con cambios menores sin un framework de migraciones completo.
    """
    try:
        async with engine.begin() as conn:
            # Alinear columnas de tasks
            await conn.execute(text("""
                ALTER TABLE IF EXISTS tasks
                ADD COLUMN IF NOT EXISTS estimated_hours DOUBLE PRECISION;
            """))
            await conn.execute(text("""
                ALTER TABLE IF EXISTS tasks
                ADD COLUMN IF NOT EXISTS actual_hours DOUBLE PRECISION;
            """))
            # Crear tablas de inventario si no existen
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS inventory_items (
                    id SERIAL PRIMARY KEY,
                    component_id INTEGER UNIQUE NOT NULL REFERENCES components(id) ON DELETE CASCADE,
                    quantity DOUBLE PRECISION NOT NULL DEFAULT 0,
                    unit_cost DOUBLE PRECISION NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NULL
                );
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS task_used_components (
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                    component_id INTEGER NULL REFERENCES components(id) ON DELETE SET NULL,
                    quantity DOUBLE PRECISION NOT NULL,
                    unit_cost_snapshot DOUBLE PRECISION NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            # Calendario laboral
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_working_days (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    weekday INTEGER NOT NULL,
                    hours DOUBLE PRECISION NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    CONSTRAINT uq_user_weekday UNIQUE (user_id, weekday)
                );
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_special_days (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    date DATE NOT NULL,
                    is_working BOOLEAN NOT NULL DEFAULT FALSE,
                    hours DOUBLE PRECISION NULL,
                    reason VARCHAR(120) NULL,
                    CONSTRAINT uq_user_date UNIQUE (user_id, date)
                );
            """))
        logger.info("✅ Migraciones simples aplicadas")
    except Exception as e:
        logger.warning(f"⚠️ Error aplicando migraciones simples: {e}")
        # No elevar para no romper el arranque; se registró la advertencia

async def drop_tables():
    """
    Elimina todas las tablas de la base de datos.
    """
    try:
        from app.models import user, asset, failure, maintenance, task, workorder, department, calendar
        
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