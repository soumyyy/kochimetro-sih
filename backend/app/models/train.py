"""
Train models and schemas aligned with Supabase schema
"""
import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Integer, Text, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .plan import InductionPlanItem
    from .depot import BayOccupancy, StablingBay
    from .maintenance import FitnessCertificate, JobCard
    from .branding import BrandingExposureLog
    from .mileage import MileageLog
    from .system import Override


class Train(Base):
    """Train roster"""
    __tablename__ = "trains"

    train_id: Mapped[str] = mapped_column(String(10), primary_key=True, index=True)
    car_count: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    brand_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    wrap_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="unknown")
    current_bay: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stabling_bays.bay_id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    bay: Mapped[Optional["StablingBay"]] = relationship(back_populates="trains")
    fitness_certificates: Mapped[List["FitnessCertificate"]] = relationship(back_populates="train")
    job_cards: Mapped[List["JobCard"]] = relationship(back_populates="train")
    exposure_logs: Mapped[List["BrandingExposureLog"]] = relationship(back_populates="train")
    mileage_logs: Mapped[List["MileageLog"]] = relationship(back_populates="train")
    bay_occupancies: Mapped[List["BayOccupancy"]] = relationship(back_populates="train")
    plan_items: Mapped[List["InductionPlanItem"]] = relationship(back_populates="train")
    overrides: Mapped[List["Override"]] = relationship(back_populates="train")


# Pydantic schemas
class TrainSchema(BaseSchema):
    """Train response schema"""
    train_id: str
    car_count: int
    brand_code: Optional[str]
    wrap_id: Optional[str]
    status: str
    current_bay: Optional[uuid.UUID]
    notes: Optional[str]


class TrainCreateSchema(BaseCreateSchema):
    """Train creation schema"""
    train_id: str
    car_count: int = 4
    brand_code: Optional[str] = None
    wrap_id: Optional[str] = None
    status: str = "standby"
    current_bay: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class TrainUpdateSchema(BaseUpdateSchema):
    """Train update schema"""
    car_count: Optional[int] = None
    brand_code: Optional[str] = None
    wrap_id: Optional[str] = None
    status: Optional[str] = None
    current_bay: Optional[uuid.UUID] = None
    notes: Optional[str] = None
