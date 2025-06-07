from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base

class WorkOrder(Base):
    __tablename__ = "workorders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    work_type = Column(String(50), nullable=False)  # preventive, corrective, emergency
    status = Column(String(50), default="open")  # open, in_progress, completed, cancelled
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    estimated_cost = Column(Float)
    actual_cost = Column(Float)
    scheduled_date = Column(DateTime)
    started_date = Column(DateTime)
    completed_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    failure_id = Column(Integer, ForeignKey("failures.id"), nullable=True)  # Relación con failure en lugar de maintenance_id
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Relationships
    asset = relationship("Asset", back_populates="workorders")
    assigned_user = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_workorders")
    created_by_user = relationship("User", foreign_keys=[created_by], back_populates="created_workorders")
    failure = relationship("Failure", back_populates="workorders")
    organization = relationship("Organization", back_populates="workorders")
    tasks = relationship("Task", back_populates="workorder")
    maintenance_records = relationship("Maintenance", back_populates="workorder")