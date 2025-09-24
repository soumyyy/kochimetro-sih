"""
Train models and schemas
"""
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .plan import InductionPlanItem, TurnoutPlan
    from .branding import TrainWrap, ServiceLog, BrandingExposureLog, MileageLog
    from .maintenance import FitnessCertificate, JobCard
    from .depot import BayOccupancy
    from .system import Override


class Train(Base):
    """Train model"""
    __tablename__ = "trains"

    train_id: Mapped[str] = mapped_column(String(10), primary_key=True, index=True)
    car_count: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    brand_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    wrap_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    current_bay: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # UUID as string
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    fitness_certificates: Mapped[List["FitnessCertificate"]] = relationship(back_populates="train")
    job_cards: Mapped[List["JobCard"]] = relationship(back_populates="train")
    train_wraps: Mapped[List["TrainWrap"]] = relationship(back_populates="train")
    service_logs: Mapped[List["ServiceLog"]] = relationship(back_populates="train")
    branding_exposure_logs: Mapped[List["BrandingExposureLog"]] = relationship(back_populates="train")
    mileage_logs: Mapped[List["MileageLog"]] = relationship(back_populates="train")
    bay_occupancies: Mapped[List["BayOccupancy"]] = relationship(back_populates="train")
    plan_items: Mapped[List["InductionPlanItem"]] = relationship(back_populates="train")
    turnout_plans: Mapped[List["TurnoutPlan"]] = relationship(back_populates="train")
    overrides: Mapped[List["Override"]] = relationship(back_populates="train")


# Pydantic schemas
class TrainSchema(BaseSchema):
    """Train response schema"""
    train_id: str
    car_count: int
    status: str
    current_bay: Optional[str]
    depot_id: str
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class TrainCreateSchema(BaseCreateSchema):
    """Train creation schema"""
    train_id: str
    car_count: int = 4
    status: str = "standby"
    current_bay: Optional[str] = None
    depot_id: str = "MUTTOM"
    notes: Optional[str] = None


class TrainUpdateSchema(BaseUpdateSchema):
    """Train update schema"""
    car_count: Optional[int] = None
    status: Optional[str] = None
    current_bay: Optional[str] = None
    depot_id: Optional[str] = None
    notes: Optional[str] = None
