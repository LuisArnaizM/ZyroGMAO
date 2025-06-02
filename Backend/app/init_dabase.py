import asyncio
import os
import sys

# Añadir el directorio principal al path para importaciones
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.database.data_seed import init_db
from app.database.mongodb import client as mongo_client, mongodb

async def init_mongodb():
    """Inicializar la base de datos MongoDB con algunos datos de sensores"""
    # Limpiar colecciones existentes
    await mongodb.sensor_readings.drop()
    
    # Insertar datos de ejemplo para sensores
    sensor_data = [
        {
            "asset_id": 1,
            "sensor_type": "temperature",
            "value": 42.5,
            "timestamp": "2025-06-01T10:00:00"
        },
        {
            "asset_id": 1,
            "sensor_type": "vibration",
            "value": 12.3,
            "timestamp": "2025-06-01T10:05:00"
        },
        {
            "asset_id": 2,
            "sensor_type": "rpm",
            "value": 1750,
            "timestamp": "2025-06-01T10:00:00"
        },
        {
            "asset_id": 3,
            "sensor_type": "voltage",
            "value": 220.5,
            "timestamp": "2025-06-01T10:00:00"
        },
        {
            "asset_id": 4,
            "sensor_type": "position",
            "value": 45.2,
            "timestamp": "2025-06-01T10:00:00"
        }
    ]
    
    await mongodb.sensor_readings.insert_many(sensor_data)
    print(f"Inserted {len(sensor_data)} sensor records into MongoDB")

if __name__ == "__main__":
    print("Initializing PostgreSQL database...")
    init_db()
    
    print("Initializing MongoDB database...")
    asyncio.run(init_mongodb())
    
    print("\nDatabase initialization completed successfully!")
    print("\nCredenciales de acceso:")
    print("------------------------")
    print("Admin: admin@example.com / admin123")
    print("Supervisor: supervisor@example.com / supervisor123")
    print("Técnico: tecnico@example.com / tecnico123")
    print("Consultor: consultor@example.com / consultor123")