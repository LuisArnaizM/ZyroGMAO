from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database.postgres import Base

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String) 
    location = Column(String)
    responsible_id = Column(Integer, ForeignKey("users.id"))
    machine_id = Column(Integer, ForeignKey("machines.id"))  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Usar strings en las relaciones
    responsible = relationship("User", back_populates="assets")
    machine = relationship("Machine", back_populates="assets")
    failures = relationship("Failure", back_populates="asset")
    maintenances = relationship("Maintenance", back_populates="asset")
    sensors = relationship("Sensor", back_populates="asset")