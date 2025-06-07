import asyncio
import sys
import os

# Añadir el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.postgres import create_tables
from app.database.data_seed import seed_database

async def main():
    """
    Inicializa la base de datos creando las tablas y poblándola con datos de prueba.
    """
    print("🚀 Iniciando configuración de la base de datos...")
    
    try:
        # Crear tablas
        print("📝 Creando tablas...")
        await create_tables()
        print("✅ Tablas creadas exitosamente")
        
        # Poblar con datos de prueba
        print("🌱 Poblando base de datos con datos de prueba...")
        await seed_database()
        print("✅ Base de datos poblada exitosamente")
        
        print("🎉 Configuración de base de datos completada!")
        
    except Exception as e:
        print(f"❌ Error durante la configuración: {e}")
        raise e

if __name__ == "__main__":
    asyncio.run(main())