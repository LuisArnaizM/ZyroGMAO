from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database.postgres import Base

class Sensor(Base):
    __tablename__ = "sensors"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    name = Column(String, nullable=False)
    sensor_type = Column(String, nullable=False)  # temperature, pressure, vibration, etc.
    location = Column(String)
    units = Column(String)  # °C, psi, mm/s, etc.
    min_value = Column(Float)  # Límite inferior normal
    max_value = Column(Float)  # Límite superior normal
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    asset = relationship("Asset", back_populates="sensors")