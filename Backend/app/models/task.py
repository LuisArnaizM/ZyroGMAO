from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base
from app.models.enums import TaskStatus, TaskPriority

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(50), default=TaskStatus.PENDING.value)  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    priority = Column(String(20), default=TaskPriority.MEDIUM.value)  # LOW, MEDIUM, HIGH
    due_date = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    completion_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True)  # Reemplaza machine_id
    workorder_id = Column(Integer, ForeignKey("workorders.id"), nullable=True)
    # organización eliminada
    # organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Quien creó la tarea
    
    # Relationships
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")
    creator = relationship("User", foreign_keys=[created_by_id], back_populates="created_tasks")
    asset = relationship("Asset", back_populates="tasks")
    component = relationship("Component", back_populates="tasks")  # Reemplaza machine
    workorder = relationship("WorkOrder", back_populates="tasks")
    # organization = relationship("Organization", back_populates="tasks")
    used_components = relationship("TaskUsedComponent", back_populates="task", cascade="all, delete-orphan")