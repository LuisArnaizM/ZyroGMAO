from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base
from sqlalchemy import String
from app.models.enums import MaintenanceStatus, MaintenanceType

class Maintenance(Base):
    __tablename__ = "maintenance"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    # Persist enums by value to match DB stored strings (e.g. 'scheduled')
    status = Column(String(40), default=MaintenanceStatus.SCHEDULED.value, nullable=False)
    maintenance_type = Column(String(40), default=MaintenanceType.PREVENTIVE.value, nullable=False)
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime)
    duration_hours = Column(Float)
    cost = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys - Maintenance puede ser para un Asset o un Component específico
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Técnico responsable
    workorder_id = Column(Integer, ForeignKey("workorders.id"), nullable=True)

    # Relationships
    asset = relationship("Asset", back_populates="maintenance_records")
    component = relationship("Component", back_populates="maintenance_records")
    technician = relationship("User", foreign_keys=[user_id], back_populates="maintenance_records")
    workorder = relationship("WorkOrder", back_populates="maintenance_records")
    
    # Relación hacia el plan (opcional)
    plan_id = Column(Integer, ForeignKey("maintenance_plans.id"), nullable=True)
    plan = relationship("MaintenancePlan", back_populates="maintenances")