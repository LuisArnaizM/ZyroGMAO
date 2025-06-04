import asyncio
import os
from sqlalchemy import create_engine, text, select, func
from app.config import settings
from app.database.postgres import Base
from app.models.user import User, UserRole
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def db_is_empty():
    """Verificar si la base de datos está vacía (no tiene usuarios)"""
    sync_url = settings.postgres_url.replace('+asyncpg', '')
    engine = create_engine(sync_url)
    
    try:
        with engine.connect() as connection:
            # Verificar si la tabla users existe y tiene datos
            result = connection.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users'"))
            table_exists = result.scalar() > 0
            
            if not table_exists:
                return True  # La tabla no existe, la BD está vacía
            
            # La tabla existe, verificar si tiene datos
            result = connection.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            return count == 0  # Si count es 0, la BD está vacía
    except Exception as e:
        print(f"Error verificando si la base de datos está vacía: {e}")
        return True  # Si hay error, consideramos que está vacía para inicializarla

def init_db(drop_tables=False):
    """Función de compatibilidad para main.py"""
    init_postgres_sync()

def init_postgres_sync():
    """Inicializar la base de datos PostgreSQL de forma síncrona"""
    # Usar URL síncrona para SQLAlchemy
    sync_url = settings.postgres_url.replace('+asyncpg', '')
    
    # Crear motor de base de datos
    engine = create_engine(sync_url)
    with engine.connect() as connection:
        # Primero verificar si la base de datos existe
        try:
            # Crear explícitamente el esquema 'public' y otorgar permisos
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS public;"))
            connection.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
            connection.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            connection.commit()
            print("✅ Esquema 'public' verificado/creado correctamente")
        except Exception as e:
            print(f"⚠️ Error al verificar/crear el esquema: {e}")
    
    # Crear todas las tablas definidas en los modelos
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas en PostgreSQL")
    
    from sqlalchemy.orm import Session
    with Session(engine) as session:
        try:
            user_count = session.query(User).count()
            if user_count > 0:
                print(f"👤 La base de datos ya tiene {user_count} usuarios. No se crearán usuarios de ejemplo.")
                # Verificar si existe el superusuario 'admin'
                admin_exists = session.query(User).filter(User.email == "admin").first() is not None
                
                if not admin_exists:
                    print("🔑 Creando superusuario 'admin'...")
                    superadmin = User(
                        email="admin",  # Email simple que servirá como nombre de usuario
                        hashed_password=pwd_context.hash("admin"),  # Contraseña simple
                        role=UserRole.admin  # Asignar rol de administrador
                    )
                    session.add(superadmin)
                    session.commit()
                    print("✅ Superusuario 'admin' creado exitosamente")
                return
                
            # Crear usuarios de ejemplo
            print("🔑 Creando usuarios de ejemplo...")
            
            # Superusuario con credenciales simples
            superadmin = User(
                email="admin",
                hashed_password=pwd_context.hash("admin"),
                role=UserRole.admin
            )
            
            # Usuarios adicionales
            admin = User(
                email="admin@example.com",
                hashed_password=pwd_context.hash("admin123"),
                role=UserRole.admin
            )
            
            supervisor = User(
                email="supervisor@example.com",
                hashed_password=pwd_context.hash("supervisor123"),
                role=UserRole.supervisor
            )
            
            tecnico = User(
                email="tecnico@example.com",
                hashed_password=pwd_context.hash("tecnico123"),
                role=UserRole.tecnico
            )
            
            consultor = User(
                email="consultor@example.com",
                hashed_password=pwd_context.hash("consultor123"),
                role=UserRole.consultor
            )
            
            # Añadir todos los usuarios
            session.add_all([superadmin, admin, supervisor, tecnico, consultor])
            session.commit()
            print("👥 Usuarios creados exitosamente")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error al crear usuarios: {e}")
            raise

async def init_mongodb():
    """Inicializar la base de datos MongoDB"""
    from app.database.mongodb import mongodb
    
    # Limpiar colecciones existentes
    await mongodb.sensor_readings.drop()
    
    # Insertar datos de ejemplo para sensores
    sensor_data = [
        {
            "sensor_id": 1,
            "asset_id": 1,
            "value": 42.5,
            "timestamp": "2023-06-01T10:00:00"
        },
        {
            "sensor_id": 2,
            "asset_id": 1,
            "value": 12.3,
            "timestamp": "2023-06-01T10:05:00"
        },
        {
            "sensor_id": 3,
            "asset_id": 2,
            "value": 1750,
            "timestamp": "2023-06-01T10:00:00"
        },
        {
            "sensor_id": 1,
            "asset_id": 3,
            "value": 220.5,
            "timestamp": "2023-06-01T10:00:00"
        },
        {
            "sensor_id": 4,
            "asset_id": 4,
            "value": 45.2,
            "timestamp": "2023-06-01T10:00:00"
        }
    ]
    
    await mongodb.sensor_readings.insert_many(sensor_data)
    print("📊 Datos insertados en MongoDB")

async def main():
    print("🚀 Inicializando bases de datos...")
    
    # PostgreSQL (síncrono)
    init_postgres_sync()
    
    # MongoDB (asíncrono)
    await init_mongodb()

if __name__ == "__main__":
    asyncio.run(main())