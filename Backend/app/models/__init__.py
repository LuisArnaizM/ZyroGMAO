# app/models/__init__.py
"""
Modelos de la aplicación.
Este archivo importa todos los modelos para asegurar que se registren con SQLAlchemy.
"""

from app.models.user import User
from app.models.asset import Asset
from app.models.component import Component
from app.models.failure import Failure
from app.models.maintenance import Maintenance
from app.models.task import Task
from app.models.workorder import WorkOrder
from app.models.inventory import InventoryItem, TaskUsedComponent
from app.models.department import Department

__all__ = [
    "User",
    "Asset",
    "Component",
    "Failure",
    "Maintenance",
    "Task",
    "WorkOrder",
    "InventoryItem",
    "TaskUsedComponent",
    "Department"
]