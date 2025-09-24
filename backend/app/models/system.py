"""
System management models and schemas
"""
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Text, JSON, TIMESTAMP, ForeignKey, Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .train import Train
    from .plan import InductionPlan
    from .user import User


class Alert(Base):
    """Alert and notification model"""
    __tablename__ = "alerts"

    alert_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("induction_plans.plan_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    plan: Mapped[Optional["InductionPlan"]] = relationship(back_populates="alerts")


class Override(Base):
    """Manual override model"""
    __tablename__ = "overrides"

    override_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    plan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("induction_plans.plan_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    train_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("trains.train_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    plan: Mapped["InductionPlan"] = relationship(back_populates="overrides")
    train: Mapped["Train"] = relationship(back_populates="overrides")
    user: Mapped[Optional["User"]] = relationship(back_populates="overrides")


# Pydantic schemas
class AlertSchema(BaseSchema):
    """Alert response schema"""
    alert_id: str
    plan_id: Optional[str]
    severity: str
    message: str
    data: Optional[Dict[str, Any]]
    resolved: bool
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    created_at: Optional[datetime]


class OverrideSchema(BaseSchema):
    """Override response schema"""
    override_id: str
    plan_id: str
    train_id: str
    reason: str
    user_id: str
    override_data: Dict[str, Any]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: Optional[datetime]
