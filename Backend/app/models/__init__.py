# app/models/__init__.py
"""
Modelos de la aplicación.
Este archivo importa todos los modelos para asegurar que se registren con SQLAlchemy.
"""

from app.models.user import User
from app.models.organization import Organization
from app.models.asset import Asset
from app.models.component import Component
from app.models.sensor import Sensor
from app.models.sensordata import SensorData
from app.models.failure import Failure
from app.models.maintenance import Maintenance
from app.models.task import Task
from app.models.workorder import WorkOrder

__all__ = [
    "User",
    "Organization",
    "Asset",
    "Component",
    "Sensor",
    "SensorData",
    "Failure",
    "Maintenance",
    "Task",
    "WorkOrder"
]