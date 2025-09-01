from sqlalchemy import Column, Integer, ForeignKey, Date, Boolean, Float, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.postgres import Base

class UserWorkingDay(Base):
    __tablename__ = "user_working_days"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    weekday = Column(Integer, nullable=False)  # 0=lunes ... 6=domingo
    hours = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'weekday', name='uq_user_weekday'),
    )

class UserSpecialDay(Base):
    __tablename__ = "user_special_days"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    is_working = Column(Boolean, nullable=False, default=False)  # False = no laborable
    hours = Column(Float, nullable=True)  # Si is_working True y hours None => usar patrón por defecto
    reason = Column(String(120), nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_user_date'),
    )
