"""
Plan models aligned with Supabase schema
"""
import uuid
from datetime import date
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import Text, JSON, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .train import Train
    from .user import User
    from .system import Alert, Override


class InductionPlan(Base):
    """Daily induction plan"""
    __tablename__ = "induction_plans"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_date: Mapped[date] = mapped_column(nullable=False, unique=True, index=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    weights_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    creator: Mapped[Optional["User"]] = relationship(back_populates="created_plans")
    plan_items: Mapped[List["InductionPlanItem"]] = relationship(back_populates="plan")
    alerts: Mapped[List["Alert"]] = relationship(back_populates="plan")
    overrides: Mapped[List["Override"]] = relationship(back_populates="plan")


class InductionPlanItem(Base):
    """Per-train decision"""
    __tablename__ = "induction_plan_items"

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("induction_plans.plan_id", ondelete="CASCADE"), nullable=False, index=True
    )
    train_id: Mapped[str] = mapped_column(
        Text, ForeignKey("trains.train_id", ondelete="CASCADE"), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    bay_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    turnout_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    km_target: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explain_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    plan: Mapped["InductionPlan"] = relationship(back_populates="plan_items")
    train: Mapped["Train"] = relationship(back_populates="plan_items")


# Pydantic schemas
class InductionPlanSchema(BaseSchema):
    """Plan response schema"""
    plan_id: uuid.UUID
    plan_date: date
    status: str
    weights_json: Dict[str, Any]
    created_by: Optional[uuid.UUID]
    notes: Optional[str]


class InductionPlanCreateSchema(BaseCreateSchema):
    """Plan creation schema"""
    plan_date: date
    weights: Optional[Dict[str, float]] = None
    notes: Optional[str] = None


class InductionPlanItemSchema(BaseSchema):
    """Plan item response schema"""
    item_id: int
    plan_id: uuid.UUID
    train_id: str
    decision: str
    bay_id: Optional[uuid.UUID]
    turnout_rank: Optional[int]
    km_target: Optional[float]
    notes: Optional[str]
    explain_json: Dict[str, Any]
