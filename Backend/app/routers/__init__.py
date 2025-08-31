"""
Routers de la aplicación.
Este archivo importa todos los routers para facilitar su importación en main.py
"""

from . import (
    auth,
    users,
    assets,
    components,  # Nuevo router
    failures,
    maintenance,
    tasks,
    workorders,
    department,
    kpi,
    inventory
)

__all__ = [
    "auth",
    "users", 
    "assets",
    "components",  # Nuevo router
    "failures",
    "maintenance",
    "tasks",
    "workorders",
    "department",
    "kpi",
    "inventory"
]