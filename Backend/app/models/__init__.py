# Importaciones explícitas para resolver las dependencias circulares
from app.models.user import User, UserRole
from app.models.machine import Machine
from app.models.asset import Asset
from app.models.sensor import Sensor
from app.models.failure import Failure
from app.models.task import Task
from app.models.maintenance import Maintenance
from app.models.workorder import WorkOrder

# Exportar todos los modelos
__all__ = [
    "User", 
    "UserRole", 
    "Machine", 
    "Asset", 
    "Sensor", 
    "Failure", 
    "Task", 
    "Maintenance", 
    "WorkOrder"
]