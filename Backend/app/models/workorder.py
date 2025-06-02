from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from app.database.postgres import Base

class WorkOrder(Base):
    __tablename__ = "work_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    maintenance_id = Column(Integer, ForeignKey("maintenance_requests.id"), nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())