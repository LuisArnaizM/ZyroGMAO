import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func  # Agregar text aquí
from app.database.postgres import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.asset import Asset
from app.models.sensor import Sensor
from app.models.failure import Failure
from app.models.maintenance import Maintenance
from app.models.task import Task
from app.models.workorder import WorkOrder
from app.models.sensordata import SensorData
from app.auth.security import get_password_hash
import logging

logger = logging.getLogger(__name__)

async def seed_database():
    """
    Puebla la base de datos con datos de prueba.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Verificar si ya hay datos - CORREGIR ESTA LÍNEA
            existing_orgs = await session.execute(text("SELECT COUNT(*) FROM organizations"))
            if existing_orgs.scalar() > 0:
                logger.info("Base de datos ya contiene datos, saltando seed...")
                return

            # Crear organizaciones
            org1 = Organization(
                name="Tech Industries Corp",
                slug="tech-industries",
                description="Empresa de tecnología industrial",
                domain="techindustries.com",
                max_users=100,
                max_assets=1000
            )
            
            org2 = Organization(
                name="Manufacturing Solutions",
                slug="manufacturing-solutions", 
                description="Soluciones de manufactura avanzada",
                domain="manufacturingsolutions.com",
                max_users=50,
                max_assets=500
            )
            
            session.add_all([org1, org2])
            await session.flush()  # Para obtener los IDs

            # Crear usuarios
            admin_user = User(
                email="admin@techindustries.com",
                username="admin",
                first_name="Administrator",
                last_name="System",
                hashed_password=get_password_hash("admin123"),
                role="Admin",
                organization_id=org1.id,
                is_active=1
            )
            
            manager_user = User(
                email="manager@techindustries.com",
                username="manager",
                first_name="Production",
                last_name="Manager",
                hashed_password=get_password_hash("manager123"),
                role="Supervisor",
                organization_id=org1.id,
                is_active=1
            )
            
            technician_user = User(
                email="tech@techindustries.com",
                username="technician",
                first_name="Lead",
                last_name="Technician",
                hashed_password=get_password_hash("tech123"),
                role="Tecnico",
                organization_id=org1.id,
                is_active=1
            )
            
            session.add_all([admin_user, manager_user, technician_user])
            await session.flush()

            # Crear activos (máquinas)
            machine1 = Asset(
                name="CNC Machine #001",
                description="High precision CNC milling machine",
                asset_type="machine",
                model="Haas VF-2",
                serial_number="HV2-2023-001",
                location="Production Floor A",
                status="operational",
                organization_id=org1.id
            )
            
            machine2 = Asset(
                name="Industrial Robot #002",
                description="6-axis industrial robot for assembly",
                asset_type="robot",
                model="KUKA KR 120",
                serial_number="KR120-2023-002",
                location="Assembly Line 1",
                status="operational",
                organization_id=org1.id
            )
            
            session.add_all([machine1, machine2])
            await session.flush()

            # Crear componentes para los assets
            from app.models.component import Component
            
            # Componentes para CNC Machine #001
            spindle = Component(
                name="Main Spindle",
                description="Primary cutting spindle",
                component_type="spindle",
                model="HSK-A63",
                serial_number="SPN-001-2023",
                location="Spindle Housing",
                status="operational",
                asset_id=machine1.id,
                organization_id=org1.id,
                maintenance_interval_days=90,
                purchase_cost=15000.0,
                current_value=12000.0
            )
            
            coolant_pump = Component(
                name="Coolant Pump",
                description="Coolant circulation pump",
                component_type="pump",
                model="CP-500",
                serial_number="CP500-2023-001",
                location="Coolant System",
                status="operational",
                asset_id=machine1.id,
                organization_id=org1.id,
                maintenance_interval_days=180,
                purchase_cost=2500.0,
                current_value=2000.0
            )
            
            # Componentes para Industrial Robot #002
            servo_motor = Component(
                name="Base Servo Motor",
                description="Base rotation servo motor",
                component_type="motor",
                model="SMX-750",
                serial_number="SMX750-2023-002",
                location="Base Joint",
                status="operational",
                asset_id=machine2.id,
                organization_id=org1.id,
                maintenance_interval_days=120,
                purchase_cost=3500.0,
                current_value=3000.0
            )
            
            gripper = Component(
                name="Pneumatic Gripper",
                description="End effector pneumatic gripper",
                component_type="gripper",
                model="PG-200",
                serial_number="PG200-2023-002",
                location="End Effector",
                status="operational",
                asset_id=machine2.id,
                organization_id=org1.id,
                maintenance_interval_days=60,
                purchase_cost=1200.0,
                current_value=1000.0
            )
            
            session.add_all([spindle, coolant_pump, servo_motor, gripper])
            await session.flush()

            # Crear sensores (algunos asociados a componentes específicos)
            temp_sensor = Sensor(
                name="Spindle Temperature Sensor",
                sensor_type="temperature",
                unit="°C",
                min_value=-50.0,
                max_value=200.0,
                component_id=spindle.id,  # Asociado al componente spindle
                organization_id=org1.id
            )
            
            vibration_sensor = Sensor(
                name="Spindle Vibration Sensor",
                sensor_type="vibration",
                unit="g",
                min_value=0.0,
                max_value=10.0,
                component_id=spindle.id,  # Asociado al componente spindle
                organization_id=org1.id
            )
            
            pressure_sensor = Sensor(
                name="Coolant Pressure Sensor",
                sensor_type="pressure",
                unit="bar",
                min_value=0.0,
                max_value=50.0,
                component_id=coolant_pump.id,  # Asociado al componente coolant_pump
                organization_id=org1.id
            )
            
            position_sensor = Sensor(
                name="Motor Position Sensor",
                sensor_type="position",
                unit="degrees",
                min_value=0.0,
                max_value=360.0,
                component_id=servo_motor.id,  # Asociado al componente servo_motor
                asset_id=machine1.id,
                organization_id=org1.id
            )
            
            # Sensor general del asset (sin componente específico)
            hydraulic_sensor = Sensor(
                name="General Hydraulic Pressure",
                sensor_type="pressure",
                unit="bar",
                min_value=0.0,
                max_value=300.0,
                asset_id=machine2.id,  # Asociado al asset directamente
                organization_id=org1.id
            )
            
            session.add_all([temp_sensor, vibration_sensor, pressure_sensor, position_sensor, hydraulic_sensor])
                unit="%",
                min_value=0.0,
                max_value=100.0,
                asset_id=machine1.id,
                organization_id=org1.id,
                component_id=coolant_pump.id  # Asociado al componente "Coolant Pump"
            )
            
            session.add_all([temp_sensor, vibration_sensor, pressure_sensor, spindle_temp_sensor, coolant_level_sensor])
            await session.flush()

            # Crear datos de sensores (últimas 24 horas)
            now = datetime.utcnow()
            sensor_data_entries = []
            
            for i in range(24):  # 24 lecturas (una por hora)
                timestamp = now - timedelta(hours=i)
                
                # Datos de temperatura (65-75°C con variación normal)
                temp_data = SensorData(
                    sensor_id=temp_sensor.id,
                    value=70.0 + (i % 5) - 2.5,  # Variación entre 67.5 y 72.5
                    timestamp=timestamp
                )
                
                # Datos de vibración (0.5-1.5g normal)
                vib_data = SensorData(
                    sensor_id=vibration_sensor.id,
                    value=1.0 + (i % 3) * 0.2 - 0.2,  # Variación entre 0.8 y 1.4
                    timestamp=timestamp
                )
                
                # Datos de presión (150-180 bar normal)
                pressure_data = SensorData(
                    sensor_id=pressure_sensor.id,
                    value=165.0 + (i % 4) * 5 - 7.5,  # Variación entre 157.5 y 172.5
                    timestamp=timestamp
                )
                
                # Datos de temperatura del husillo (20-40°C con variación normal)
                spindle_temp_data = SensorData(
                    sensor_id=spindle_temp_sensor.id,
                    value=30.0 + (i % 5) - 2.5,  # Variación entre 27.5 y 32.5
                    timestamp=timestamp
                )
                
                # Datos del nivel de refrigerante (30-70% con variación normal)
                coolant_level_data = SensorData(
                    sensor_id=coolant_level_sensor.id,
                    value=50.0 + (i % 4) * 5 - 10,  # Variación entre 30 y 70
                    timestamp=timestamp
                )
                
                sensor_data_entries.extend([temp_data, vib_data, pressure_data, spindle_temp_data, coolant_level_data])
            
            session.add_all(sensor_data_entries)

            # Crear algunas fallas históricas
            failure1 = Failure(
                description="Machine temperature exceeded normal operating range",
                severity="medium",
                status="resolved",
                asset_id=machine1.id,
                reported_by=technician_user.id,
                organization_id=org1.id,
                reported_date=now - timedelta(days=7),
                resolved_date=now - timedelta(days=6)
            )
            
            failure2 = Failure(
                description="Sudden drop in hydraulic pressure during operation",
                severity="high",
                status="reported",
                asset_id=machine2.id,
                reported_by=technician_user.id,
                organization_id=org1.id,
                reported_date=now - timedelta(days=2)
            )
            
            session.add_all([failure1, failure2])
            await session.flush()

            # Crear órdenes de trabajo
            work_order1 = WorkOrder(
                title="Preventive Maintenance - CNC Machine",
                description="Monthly preventive maintenance for CNC machine",
                priority="medium",
                status="completed",
                asset_id=machine1.id,
                assigned_to=technician_user.id,
                created_by=manager_user.id,
                organization_id=org1.id,
                due_date=now + timedelta(days=5),
                completed_at=now - timedelta(days=1)
            )
            
            work_order2 = WorkOrder(
                title="Hydraulic System Inspection",
                description="Investigate and fix hydraulic pressure issues",
                priority="high",
                status="in_progress",
                asset_id=machine2.id,
                assigned_to=technician_user.id,
                created_by=manager_user.id,
                organization_id=org1.id,
                due_date=now + timedelta(days=2),
                failure_id=failure2.id
            )
            
            session.add_all([work_order1, work_order2])
            await session.flush()

            # Crear tareas para las órdenes de trabajo
            task1 = Task(
                title="Replace air filters",
                description="Replace all air filters in the CNC machine",
                status="completed",
                priority="medium",
                assigned_to=technician_user.id,
                created_by_id=manager_user.id,
                asset_id=machine1.id,
                workorder_id=work_order1.id,
                organization_id=org1.id,
                due_date=now + timedelta(days=1)
            )
            
            task2 = Task(
                title="Check hydraulic fluid levels",
                description="Inspect and top up hydraulic fluid if necessary",
                status="in_progress",
                priority="high",
                assigned_to=technician_user.id,
                created_by_id=manager_user.id,
                asset_id=machine2.id,
                workorder_id=work_order2.id,
                organization_id=org1.id,
                due_date=now + timedelta(days=2)
            )
            
            task3 = Task(
                title="Inspect hydraulic seals",
                description="Check all hydraulic seals for leaks or damage",
                status="pending",
                priority="medium",
                assigned_to=technician_user.id,
                created_by_id=manager_user.id,
                asset_id=machine2.id,
                workorder_id=work_order2.id,
                organization_id=org1.id,
                due_date=now + timedelta(days=3)
            )
            
            session.add_all([task1, task2, task3])

            # Crear registros de mantenimiento
            maintenance1 = Maintenance(
                description="Completed monthly preventive maintenance including filter replacement and general inspection",
                maintenance_type="preventive",
                status="completed",
                asset_id=machine1.id,
                user_id=technician_user.id,
                organization_id=org1.id,
                workorder_id=work_order1.id,
                scheduled_date=now - timedelta(days=1),
                completed_date=now - timedelta(days=1),
                duration_hours=3.0,
                cost=150.00
            )
            
            session.add(maintenance1)

            await session.commit()
            logger.info("✅ Base de datos poblada exitosamente con datos de prueba")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error poblando la base de datos: {e}")
            raise e