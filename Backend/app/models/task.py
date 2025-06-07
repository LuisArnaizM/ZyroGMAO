from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, cancelled
    priority = Column(String(20), default="medium")  # low, medium, high
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True)  # Reemplaza machine_id
    workorder_id = Column(Integer, ForeignKey("workorders.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Quien creó la tarea
    
    # Relationships
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")
    creator = relationship("User", foreign_keys=[created_by_id], back_populates="created_tasks")
    asset = relationship("Asset", back_populates="tasks")
    component = relationship("Component", back_populates="tasks")  # Reemplaza machine
    workorder = relationship("WorkOrder", back_populates="tasks")
    organization = relationship("Organization", back_populates="tasks")