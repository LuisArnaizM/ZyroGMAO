import asyncio
import sys
import os
import asyncpg

# Añadir el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

# Importar TODOS los modelos AQUÍ al nivel del módulo
from app.models.user import User
from app.models.component import Component
from app.models.asset import Asset
from app.models.failure import Failure
from app.models.maintenance import Maintenance
from app.models.task import Task
from app.models.workorder import WorkOrder

async def force_clean_database():
    """
    Limpia completamente la base de datos eliminando y recreando el esquema.
    """
    try:
        # Construir URL para asyncpg
        host = settings.POSTGRES_SERVER or "localhost"
        # Si estamos en Docker, usar el host "db", si no, usar localhost
        if os.getenv("DOCKER_ENV") == "true" or os.path.exists("/.dockerenv"):
            host = "db"
        elif host == "db":
            host = "localhost"
            
        database_url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{host}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        
        print(f"🔗 Conectando a: {host}:{settings.POSTGRES_PORT}")
        # Conectar directamente a PostgreSQL
        conn = await asyncpg.connect(database_url)
        
        print("🧹 Eliminando esquema completo...")
        # Eliminar y recrear el esquema public con CASCADE para forzar
        await conn.execute("DROP SCHEMA IF EXISTS public CASCADE;")
        await conn.execute("CREATE SCHEMA public;")
        await conn.execute("GRANT ALL ON SCHEMA public TO postgres;")
        await conn.execute("GRANT ALL ON SCHEMA public TO public;")
        
        await conn.close()
        print("✅ Esquema limpiado exitosamente")
        
    except Exception as e:
        print(f"❌ Error limpiando la base de datos: {e}")
        raise e

async def main():
    """
    Reset completo de la base de datos con importaciones forzadas.
    """
    print("🔄 Iniciando reset limpio de la base de datos...")
    
    try:
        # Forzar limpieza completa
        await force_clean_database()
        
        # Importar las funciones después de limpiar
        from app.database.postgres import create_tables
        from app.database.data_seed import seed_database
        
        # Los modelos ya están importados al nivel del módulo
        print(f"📋 Modelos registrados: {[User.__name__, Component.__name__, Asset.__name__]}")
        
        # Crear tablas nuevamente
        print("📝 Creando tablas...")
        await create_tables()
        print("✅ Tablas creadas exitosamente")
        
        # Poblar con datos de prueba
        print("🌱 Poblando base de datos con datos de prueba...")
        await seed_database()
        print("✅ Base de datos poblada exitosamente")
        
        print("🎉 Reset de base de datos completado!")
        
    except Exception as e:
        print(f"❌ Error durante el reset: {e}")
        import traceback
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    asyncio.run(main())