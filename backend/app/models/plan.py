"""
Induction plan models and schemas
"""
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import date, datetime
from sqlalchemy import String, Date, Text, JSON, TIMESTAMP, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .train import Train
    from .depot import DepotRoute
    from .user import User
    from .system import Alert, Override


class InductionPlan(Base):
    """Induction plan model"""
    __tablename__ = "induction_plans"

    plan_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True)
    plan_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    weights_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Override Base timestamps since they don't exist in existing DB schema
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    creator: Mapped[Optional["User"]] = relationship(back_populates="created_plans")
    plan_items: Mapped[List["InductionPlanItem"]] = relationship(back_populates="plan")
    turnout_plans: Mapped[List["TurnoutPlan"]] = relationship(back_populates="plan")
    alerts: Mapped[List["Alert"]] = relationship(back_populates="plan")
    overrides: Mapped[List["Override"]] = relationship(back_populates="plan")


class InductionPlanItem(Base):
    """Individual train decisions within a plan"""
    __tablename__ = "induction_plan_items"

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
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
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    bay_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    turnout_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    km_target: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explain_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    plan: Mapped["InductionPlan"] = relationship(back_populates="plan_items")
    train: Mapped["Train"] = relationship(back_populates="plan_items")


class TurnoutPlan(Base):
    """Morning turnout sequencing"""
    __tablename__ = "turnout_plan"

    turnout_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    plan_id: Mapped[str] = mapped_column(
        String(20),
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
    route_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("depot_routes.route_id"),
        nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_departure: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    actual_departure: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    delay_minutes: Mapped[int] = mapped_column(default=0)

    # Relationships
    plan: Mapped["InductionPlan"] = relationship(back_populates="turnout_plans")
    train: Mapped["Train"] = relationship(back_populates="turnout_plans")
    route: Mapped["DepotRoute"] = relationship()


# Pydantic schemas
class PlanWeightsSchema(BaseSchema):
    """Optimization weights schema"""
    w_risk: float = 1.0
    w_brand: float = 0.6
    w_mileage: float = 0.2
    w_clean: float = 0.4
    w_shunt: float = 0.15
    w_override: float = 3.0


class InductionPlanSchema(BaseSchema):
    """Plan response schema"""
    plan_id: str
    plan_date: date
    status: str
    weights_json: Dict[str, Any]
    day_type: str
    created_by: Optional[str]
    finalized_at: Optional[datetime]
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class InductionPlanCreateSchema(BaseCreateSchema):
    """Plan creation schema"""
    plan_date: date
    weights: Optional[PlanWeightsSchema] = None
    day_type: str
    notes: Optional[str] = None


class InductionPlanItemSchema(BaseSchema):
    """Plan item response schema"""
    item_id: str
    plan_id: str
    train_id: str
    decision: str
    bay_id: Optional[str]
    turnout_rank: Optional[int]
    km_target: Optional[float]
    explain_json: Dict[str, Any]
    manual_override: bool
    override_reason: Optional[str]
    created_at: Optional[datetime]


class TurnoutPlanSchema(BaseSchema):
    """Turnout plan response schema"""
    turnout_id: str
    plan_id: str
    train_id: str
    route_id: str
    rank: int
    planned_departure: Optional[datetime]
    actual_departure: Optional[datetime]
    delay_minutes: int
    created_at: Optional[datetime]
