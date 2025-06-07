"""
Routers de la aplicación.
Este archivo importa todos los routers para facilitar su importación en main.py
"""

from . import (
    auth,
    users,
    organization,
    assets,
    components,  # Nuevo router
    sensors,
    failures,
    maintenance,
    tasks,
    workorders
)

__all__ = [
    "auth",
    "users", 
    "organization",
    "assets",
    "components",  # Nuevo router
    "sensors",
    "failures",
    "maintenance",
    "tasks",
    "workorders"
]