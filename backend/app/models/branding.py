"""
Branding-related models aligned with Supabase schema
"""
from datetime import date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Text, Numeric, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .train import Train


class BrandingCampaign(Base):
    """Branding campaign definition"""
    __tablename__ = "branding_campaigns"

    wrap_id: Mapped[str] = mapped_column(Text, primary_key=True)
    advertiser: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    weekly_target_hours: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    min_daily_hours: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    penalty_weight: Mapped[float] = mapped_column(Numeric, nullable=False, default=1)


class BrandingExposureLog(Base):
    """Daily exposure tracking"""
    __tablename__ = "branding_exposure_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    train_id: Mapped[str] = mapped_column(
        Text, ForeignKey("trains.train_id", ondelete="CASCADE"), nullable=False, index=True
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    exposure_hours: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)

    # Relationships
    train: Mapped["Train"] = relationship(back_populates="exposure_logs")


# Pydantic schemas
class BrandingCampaignSchema(BaseSchema):
    """Campaign response schema"""
    wrap_id: str
    advertiser: str
    start_date: date
    end_date: date
    weekly_target_hours: float
    min_daily_hours: float
    penalty_weight: float


class BrandingExposureLogSchema(BaseSchema):
    """Exposure log response schema"""
    id: int
    train_id: str
    log_date: date
    exposure_hours: float
    wrap_id: Optional[str]
