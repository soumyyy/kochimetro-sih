"""
Branding and sponsorship models and schemas
"""
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import date, datetime
from sqlalchemy import String, Integer, Numeric, Text, Date, JSON, ForeignKey, Boolean, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .train import Train


class BrandingCampaign(Base):
    """Branding campaign model"""
    __tablename__ = "branding_campaigns"

    campaign_id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True)
    sponsor_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("sponsors.sponsor_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    campaign_name: Mapped[str] = mapped_column(String(100), nullable=False)
    promised_hours_per_day: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    rolling_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    penalty_weight: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, default=1.0)
    target_audience: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    campaign_start: Mapped[date] = mapped_column(Date, nullable=False)
    campaign_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    budget_allocated: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    actual_spent: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # Relationships
    sponsor: Mapped["Sponsor"] = relationship(back_populates="campaigns")
    train_wraps: Mapped[List["TrainWrap"]] = relationship(back_populates="campaign")
    exposure_logs: Mapped[List["BrandingExposureLog"]] = relationship(back_populates="campaign")


class TrainWrap(Base):
    """Train wrap/branding assignment"""
    __tablename__ = "train_wraps"

    wrap_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    train_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("trains.train_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    campaign_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("branding_campaigns.campaign_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    wrap_type: Mapped[str] = mapped_column(String(20), nullable=False)
    installation_date: Mapped[date] = mapped_column(Date, nullable=False)
    removal_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    active_from: Mapped[date] = mapped_column(Date, nullable=False)
    active_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    quality_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    train: Mapped["Train"] = relationship(back_populates="train_wraps")
    campaign: Mapped["BrandingCampaign"] = relationship(back_populates="train_wraps")


class BrandingExposureLog(Base):
    """Branding exposure tracking"""
    __tablename__ = "branding_exposure_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("trains.train_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    exposure_hours: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)

    # Relationships
    train: Mapped["Train"] = relationship()


class ServiceLog(Base):
    """Service log for operational tracking"""
    __tablename__ = "service_log"

    log_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    train_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("trains.train_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    planned_service: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    actual_service: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    service_start: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    service_end: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    service_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    route_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delay_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    weather_conditions: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    incidents: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    train: Mapped["Train"] = relationship(back_populates="service_logs")


class MileageLog(Base):
    """Mileage tracking"""
    __tablename__ = "mileage_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("trains.train_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    km_run: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0)

    # Relationships
    train: Mapped["Train"] = relationship()


# Pydantic schemas
class SponsorSchema(BaseSchema):
    """Sponsor response schema"""
    sponsor_id: str
    name: str
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    contract_start: date
    contract_end: Optional[date]
    penalty_rate_per_hour: float
    payment_terms: Optional[str]
    active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class BrandingCampaignSchema(BaseSchema):
    """Campaign response schema"""
    campaign_id: str
    sponsor_id: str
    campaign_name: str
    promised_hours_per_day: float
    rolling_window_days: int
    penalty_weight: float
    target_audience: Optional[str]
    campaign_start: date
    campaign_end: Optional[date]
    status: str
    budget_allocated: Optional[float]
    actual_spent: float
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class TrainWrapSchema(BaseSchema):
    """Train wrap response schema"""
    wrap_id: str
    train_id: str
    campaign_id: str
    wrap_type: str
    installation_date: date
    removal_date: Optional[date]
    active_from: date
    active_to: Optional[date]
    cost: Optional[float]
    quality_check_passed: bool
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class BrandingExposureLogSchema(BaseSchema):
    """Exposure log response schema"""
    exposure_id: str
    date: date
    train_id: str
    campaign_id: str
    exposure_minutes: int
    peak_hour_multiplier: float
    calculated_value: float
    created_at: Optional[datetime]


class ServiceLogSchema(BaseSchema):
    """Service log response schema"""
    log_id: str
    date: date
    train_id: str
    planned_service: bool
    actual_service: bool
    service_start: Optional[datetime]
    service_end: Optional[datetime]
    service_minutes: Optional[int]
    route_code: Optional[str]
    delay_minutes: int
    delay_reason: Optional[str]
    weather_conditions: Optional[str]
    incidents: Optional[Dict[str, Any]]
    created_at: Optional[datetime]


class MileageLogSchema(BaseSchema):
    """Mileage log response schema"""
    log_id: str
    date: date
    train_id: str
    km_run: float
    source: str
    route_start: Optional[str]
    route_end: Optional[str]
    energy_consumption_kwh: Optional[float]
    created_at: Optional[datetime]
