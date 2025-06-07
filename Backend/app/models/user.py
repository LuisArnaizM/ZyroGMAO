from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from app.database.postgres import Base

class UserRole(str, Enum):
    admin = "Admin"
    supervisor = "Supervisor"
    tecnico = "Tecnico"
    consultor = "Consultor"
    org_admin = "OrgAdmin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.consultor)
    is_active = Column(Integer, default=1)  # 1 = activo, 0 = inactivo
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Key para organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to", back_populates="assignee")
    created_tasks = relationship("Task", foreign_keys="Task.created_by_id", back_populates="creator")
    responsible_assets = relationship("Asset", foreign_keys="Asset.responsible_id", back_populates="responsible")
    responsible_components = relationship("Component", foreign_keys="Component.responsible_id", back_populates="responsible")
    created_workorders = relationship("WorkOrder", foreign_keys="WorkOrder.created_by", back_populates="created_by_user")
    assigned_workorders = relationship("WorkOrder", foreign_keys="WorkOrder.assigned_to", back_populates="assigned_user")
    maintenance_records = relationship("Maintenance", foreign_keys="Maintenance.user_id", back_populates="technician")
    reported_failures = relationship("Failure", foreign_keys="Failure.reported_by", back_populates="reported_by_user")