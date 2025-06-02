from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.database.postgres import Base
import enum

class UserRole(str, enum.Enum):
    admin = "Admin"
    supervisor = "Supervisor"
    tecnico = "Tecnico"
    consultor = "Consultor"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default=UserRole.consultor, nullable=False)
    
    # Relaciones
    assets = relationship("Asset", back_populates="responsible")
    machines = relationship("Machine", back_populates="responsible")
    assigned_tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assigned_to")
    created_tasks = relationship("Task", back_populates="creator", foreign_keys="Task.created_by_id")
    maintenances = relationship("Maintenance", back_populates="user")