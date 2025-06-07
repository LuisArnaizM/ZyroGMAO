from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base

class Maintenance(Base):
    __tablename__ = "maintenance"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="scheduled")  # scheduled, in_progress, completed, cancelled
    maintenance_type = Column(String(50), default="preventive")  # preventive, corrective, predictive
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
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Relationships
    asset = relationship("Asset", back_populates="maintenance_records")
    component = relationship("Component", back_populates="maintenance_records")
    technician = relationship("User", foreign_keys=[user_id], back_populates="maintenance_records")
    workorder = relationship("WorkOrder", back_populates="maintenance_records")
    organization = relationship("Organization", back_populates="maintenance_records")