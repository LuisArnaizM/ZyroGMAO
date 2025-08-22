from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base
from app.models.enums import PlanType

class MaintenancePlan(Base):
    __tablename__ = "maintenance_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)

    plan_type = Column(String(40), default=PlanType.PREVENTIVE.value, nullable=False)

    frequency_days = Column(Integer, nullable=True)   
    frequency_weeks = Column(Integer, nullable=True) 
    frequency_months = Column(Integer, nullable=True)

    # Información estimada
    estimated_duration = Column(Float)
    estimated_cost = Column(Float)

    # Fechas de control
    start_date = Column(DateTime, nullable=False, server_default=func.now())
    next_due_date = Column(DateTime, nullable=True)
    last_execution_date = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True)

    asset = relationship("Asset", back_populates="maintenance_plans")
    component = relationship("Component", back_populates="maintenance_plans")

    # Un plan genera múltiples WorkOrders
    workorders = relationship("WorkOrder", back_populates="plan", cascade="all, delete-orphan")

    # Un plan tiene múltiples ejecuciones registradas en Maintenance
    maintenances = relationship("Maintenance", back_populates="plan", cascade="all, delete-orphan")
