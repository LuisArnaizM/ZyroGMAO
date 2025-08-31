from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base
from sqlalchemy import String
from app.models.enums import AssetStatus

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    asset_type = Column(String(50), nullable=False)
    model = Column(String(100))
    serial_number = Column(String(100), unique=True, index=True)
    location = Column(String(200))
    # Persist status as plain string to avoid strict Enum mapping errors with legacy DB values
    status = Column(String(50), default=AssetStatus.ACTIVE.value, nullable=False)
    
    # Fechas
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    purchase_date = Column(DateTime(timezone=True))
    warranty_expiry = Column(DateTime(timezone=True))
    
    # Información adicional
    purchase_cost = Column(Float)
    current_value = Column(Float)
    responsible_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Usuario responsable
    responsible = relationship("User", back_populates="responsible_assets")
    
    # Componentes hijos - Esta es la nueva estructura jerárquica
    components = relationship("Component", back_populates="asset", cascade="all, delete-orphan")
    
    # Otras relaciones mantenidas para el asset principal
    failures = relationship("Failure", back_populates="asset")
    maintenance_records = relationship("Maintenance", back_populates="asset")
    workorders = relationship("WorkOrder", back_populates="asset")
    tasks = relationship("Task", back_populates="asset")
    maintenance_plans = relationship("MaintenancePlan", back_populates="asset", cascade="all, delete-orphan")
