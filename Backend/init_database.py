import asyncio
import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Añadir el directorio principal al path para importaciones
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

try:
    # Importar explícitamente todos los modelos para resolver referencias circulares
    from app.models import User, Asset, Machine, Task, Failure, Maintenance, WorkOrder, Sensor, UserRole
    
    # Configurar mappers explícitamente
    from sqlalchemy.orm import configure_mappers
    configure_mappers()
    
    from app.database.data_seed import init_postgres_sync
    from app.database.mongodb import mongodb
    
    async def init_mongodb():
        """Inicializar la base de datos MongoDB con algunos datos de sensores"""
        try:
            # Limpiar colecciones existentes
            await mongodb.sensor_readings.drop()
            
            # Insertar datos de ejemplo para sensores
            sensor_data = [
                {
                    "sensor_id": 1,
                    "asset_id": 1,
                    "sensor_type": "temperature",
                    "value": 42.5,
                    "timestamp": "2025-06-01T10:00:00"
                },
                {
                    "sensor_id": 2,
                    "asset_id": 1,
                    "sensor_type": "vibration",
                    "value": 12.3,
                    "timestamp": "2025-06-01T10:05:00"
                },
                {
                    "sensor_id": 3,
                    "asset_id": 2,
                    "sensor_type": "rpm",
                    "value": 1750,
                    "timestamp": "2025-06-01T10:00:00"
                },
                {
                    "sensor_id": 1,
                    "asset_id": 3,
                    "sensor_type": "voltage",
                    "value": 220.5,
                    "timestamp": "2025-06-01T10:00:00"
                },
                {
                    "sensor_id": 4,
                    "asset_id": 4,
                    "sensor_type": "position",
                    "value": 45.2,
                    "timestamp": "2025-06-01T10:00:00"
                }
            ]
            
            await mongodb.sensor_readings.insert_many(sensor_data)
            logging.info(f"✅ Insertados {len(sensor_data)} registros de sensores en MongoDB")
        except Exception as e:
            logging.error(f"❌ Error al inicializar MongoDB: {e}")
            raise
    
    if __name__ == "__main__":
        try:
            logging.info("🔄 Inicializando base de datos PostgreSQL...")
            init_postgres_sync()
            
            logging.info("🔄 Inicializando base de datos MongoDB...")
            asyncio.run(init_mongodb())
            
            logging.info("\n✨ ¡Inicialización completada con éxito!")
            logging.info("\nCredenciales de acceso:")
            logging.info("------------------------")
            logging.info("Admin: admin@example.com / admin123")
            logging.info("Supervisor: supervisor@example.com / supervisor123")
            logging.info("Técnico: tecnico@example.com / tecnico123")
            logging.info("Consultor: consultor@example.com / consultor123")
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            import traceback
            logging.error(traceback.format_exc())
            sys.exit(1)

except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("Asegúrate de tener instalados todos los paquetes necesarios:")
    print("pip install psycopg2-binary sqlalchemy motor")
    sys.exit(1)