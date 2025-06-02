from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.postgres import Base
from app.config import settings
from passlib.context import CryptContext

# Importar todos los modelos para que SQLAlchemy los reconozca
from app.models.user import User, UserRole
from app.models.asset import Asset
from app.models.machine import Machine
from app.models.task import Task
from app.models.failure import Failure
from app.models.maintenance import Maintenance
from app.models.workorder import WorkOrder
from app.models.sensor import Sensor

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def db_is_empty():
    from sqlalchemy import create_engine, select, func
    from app.config import settings
    from app.models.user import User
    
    sync_url = settings.postgres_url.replace('+asyncpg', '')
    engine = create_engine(sync_url)
    
    try:
        with engine.connect() as connection:
            # Verificar si la tabla users existe y tiene datos
            result = connection.execute(select(func.count()).select_from(User.__table__))
            count = result.scalar()
            return count == 0
    except Exception:
        # Si hay error (ej: tabla no existe), consideramos que está vacía
        return True
    
def init_db():
    # Usar una URL de conexión sincrónica para la inicialización
    sync_url = settings.postgres_url.replace('+asyncpg', '')
    engine = create_engine(sync_url)
    
    # Crear todas las tablas
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Crear una sesión para insertar datos iniciales
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Crear usuarios por defecto
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
        
        db.add_all([admin, supervisor, tecnico, consultor])
        db.commit()
        
        # Crear máquinas de ejemplo
        machine1 = Machine(
            name="Línea de Producción A",
            description="Línea principal de ensamblaje",
            location="Nave 1",
            responsible_id=2  # supervisor
        )
        
        machine2 = Machine(
            name="Línea de Producción B",
            description="Línea secundaria de ensamblaje",
            location="Nave 2",
            responsible_id=2  # supervisor
        )
        
        machine3 = Machine(
            name="Robot Soldador",
            description="Robot de soldadura automática",
            location="Nave 1",
            responsible_id=3  # tecnico
        )
        
        db.add_all([machine1, machine2, machine3])
        db.commit()
        
        # Crear activos de ejemplo
        asset1 = Asset(
            name="Motor Principal",
            description="Motor eléctrico 30kW",
            location="Línea A - Sección 1",
            responsible_id=3,  # tecnico
            machine_id=1  # Línea de Producción A
        )
        
        asset2 = Asset(
            name="Transportador",
            description="Cinta transportadora",
            location="Línea A - Sección 2",
            responsible_id=3,  # tecnico
            machine_id=1
        )
        
        asset3 = Asset(
            name="Panel de Control",
            description="Panel principal de control",
            location="Línea B - Sección 1",
            responsible_id=2,  # supervisor
            machine_id=2
        )
        
        asset4 = Asset(
            name="Brazo Robótico",
            description="Brazo robótico para soldadura",
            location="Nave 1 - Celda 3",
            responsible_id=3,  # tecnico
            machine_id=3
        )
        
        db.add_all([asset1, asset2, asset3, asset4])
        db.commit()
        
        # Crear sensores de ejemplo
        sensor1 = Sensor(
            asset_id=1,  # Motor Principal
            name="Temperatura Motor",
            sensor_type="temperature",
            location="Estator",
            units="°C",
            min_value=30.0,
            max_value=80.0
        )

        sensor2 = Sensor(
            asset_id=1,  # Motor Principal
            name="Vibración Motor",
            sensor_type="vibration",
            location="Carcasa",
            units="mm/s",
            min_value=0.0,
            max_value=5.0
        )

        sensor3 = Sensor(
            asset_id=2,  # Transportador
            name="Velocidad Transportador",
            sensor_type="rpm",
            location="Eje motor",
            units="RPM",
            min_value=100.0,
            max_value=2000.0
        )

        sensor4 = Sensor(
            asset_id=4,  # Brazo Robótico
            name="Posición Eje Z",
            sensor_type="position",
            location="Actuador",
            units="mm",
            min_value=0.0,
            max_value=500.0
        )

        db.add_all([sensor1, sensor2, sensor3, sensor4])
        db.commit()
        # Crear fallos de ejemplo
        failure1 = Failure(
            asset_id=1,  # Motor Principal
            description="Ruido anormal en el motor",
            status="open"
        )
        
        failure2 = Failure(
            asset_id=2,  # Transportador
            description="La cinta se detiene intermitentemente",
            status="in_progress"
        )
        
        failure3 = Failure(
            asset_id=4,  # Brazo Robótico
            description="Error de calibración en eje Z",
            status="closed"
        )
        
        db.add_all([failure1, failure2, failure3])
        db.commit()
        
        # Crear tareas de ejemplo
        task1 = Task(
            name="Revisar Motor Principal",
            description="Inspección completa del motor por ruido anormal",
            assigned_to=3,  # tecnico
            machine_id=1,  # Línea de Producción A
            due_date="2025-06-10T10:00:00",
            created_by_id=2  # supervisor
        )
        
        task2 = Task(
            name="Mantenimiento de cinta transportadora",
            description="Revisión y lubricación de cinta transportadora",
            assigned_to=3,  # tecnico
            machine_id=1,  # Línea de Producción A
            due_date="2025-06-15T14:00:00",
            created_by_id=2  # supervisor
        )
        
        task3 = Task(
            name="Calibración de robot",
            description="Calibrar ejes del robot soldador",
            assigned_to=3,  # tecnico
            machine_id=3,  # Robot Soldador
            due_date="2025-06-08T09:00:00",
            created_by_id=1  # admin
        )
        
        db.add_all([task1, task2, task3])
        db.commit()
        
        # Crear registros de mantenimiento
        maintenance1 = Maintenance(
            asset_id=2,  # Transportador
            user_id=3,  # tecnico
            description="Mantenimiento preventivo de cinta transportadora",
            status="pending"
        )
        
        maintenance2 = Maintenance(
            asset_id=4,  # Brazo Robótico
            user_id=3,  # tecnico
            description="Calibración y ajuste de brazo robótico",
            status="completed"
        )
        
        db.add_all([maintenance1, maintenance2])
        db.commit()
        
        # Crear órdenes de trabajo
        workorder1 = WorkOrder(
            task_id=1,  # Revisar Motor Principal
            maintenance_id=1,  # Relacionado con el primer fallo
            description="Orden de trabajo para revisión de motor",
            status="pending",
            created_by="supervisor@example.com"
        )
        
        workorder2 = WorkOrder(
            task_id=2,  # Mantenimiento de cinta transportadora
            maintenance_id=2,  # Relacionado con el segundo fallo
            description="Orden de trabajo para mantenimiento de transportador",
            status="in_progress",
            created_by="admin@example.com"
        )
        
        workorder3 = WorkOrder(
            task_id=3,  # Calibración de robot
            maintenance_id=3,  # Relacionado con el tercer fallo
            description="Orden de trabajo para calibración de robot",
            status="completed",
            created_by="supervisor@example.com"
        )
        
        db.add_all([workorder1, workorder2, workorder3])
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error during database initialization: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")