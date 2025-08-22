from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    component_id = Column(Integer, ForeignKey("components.id"), unique=True, nullable=False)
    quantity = Column(Float, nullable=False, default=0)
    unit_cost = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    component = relationship("Component", back_populates="inventory_item")


class TaskUsedComponent(Base):
    __tablename__ = "task_used_components"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True)
    quantity = Column(Float, nullable=False)
    unit_cost_snapshot = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="used_components")
    component = relationship("Component", back_populates="used_in_tasks")
