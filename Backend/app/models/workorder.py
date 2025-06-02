from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database.postgres import Base

class WorkOrder(Base):
    __tablename__ = "workorders"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    maintenance_id = Column(Integer, ForeignKey("failures.id"), nullable=False)
    status = Column(String, default="pending")
    description = Column(String)
    created_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    task = relationship("Task", back_populates="workorders")
    failure = relationship("Failure", back_populates="workorders")