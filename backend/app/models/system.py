"""
System-level models (alerts, overrides)
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import Text, JSON, Boolean, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .plan import InductionPlan
    from .train import Train
    from .user import User


class Alert(Base):
    """Plan-level alert"""
    __tablename__ = "alerts"

    alert_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("induction_plans.plan_id", ondelete="CASCADE"), nullable=False, index=True
    )
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    plan: Mapped["InductionPlan"] = relationship(back_populates="alerts")


class Override(Base):
    """Manual override record"""
    __tablename__ = "overrides"

    override_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("induction_plans.plan_id", ondelete="CASCADE"), nullable=False, index=True
    )
    train_id: Mapped[str] = mapped_column(
        Text, ForeignKey("trains.train_id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    plan: Mapped["InductionPlan"] = relationship(back_populates="overrides")
    train: Mapped["Train"] = relationship(back_populates="overrides")
    user: Mapped[Optional["User"]] = relationship(back_populates="overrides")


# Pydantic schemas
class AlertSchema(BaseSchema):
    """Alert response schema"""
    alert_id: int
    plan_id: uuid.UUID
    severity: str
    message: str
    data: Dict[str, Any]
    resolved: bool
    created_at: datetime


class OverrideSchema(BaseSchema):
    """Override response schema"""
    override_id: uuid.UUID
    plan_id: uuid.UUID
    train_id: str
    reason: str
    user_id: Optional[uuid.UUID]
