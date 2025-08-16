from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Hierarchy and ownership
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    parent = relationship("Department", remote_side=[id], back_populates="children")
    children = relationship("Department", back_populates="parent")
    organization = relationship("Organization", back_populates="departments")
    manager = relationship("User", foreign_keys=[manager_id])
    users = relationship("User", back_populates="department", foreign_keys="User.department_id")
