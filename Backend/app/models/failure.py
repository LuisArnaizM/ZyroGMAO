from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base

class Failure(Base):
    __tablename__ = "failures"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="reported")  # reported, investigating, resolved
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    reported_date = Column(DateTime(timezone=True), server_default=func.now())
    resolved_date = Column(DateTime, nullable=True)
    resolution_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys - Failure puede estar en un Asset o en un Component específico
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True)
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Relationships
    asset = relationship("Asset", back_populates="failures")
    component = relationship("Component", back_populates="failures")
    reported_by_user = relationship("User", foreign_keys=[reported_by], back_populates="reported_failures")
    organization = relationship("Organization", back_populates="failures")
    workorders = relationship("WorkOrder", back_populates="failure")