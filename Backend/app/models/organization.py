from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=True, unique=True)  # URL slug para la organización
    description = Column(Text)
    domain = Column(String(100), nullable=True, unique=True)  # Para multi-tenant por dominio
    is_active = Column(Boolean, default=True)
    max_users = Column(Integer, default=50)  # Límite de usuarios
    max_assets = Column(Integer, default=500)  # Límite de assets
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="organization")
    assets = relationship("Asset", back_populates="organization")
    components = relationship("Component", back_populates="organization")
    tasks = relationship("Task", back_populates="organization")
    failures = relationship("Failure", back_populates="organization")
    maintenance_records = relationship("Maintenance", back_populates="organization")
    workorders = relationship("WorkOrder", back_populates="organization")
    sensors = relationship("Sensor", back_populates="organization")
    departments = relationship("Department", back_populates="organization")