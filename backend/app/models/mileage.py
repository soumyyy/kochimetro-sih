"""
Mileage tracking model
"""
from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import Numeric, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema

if TYPE_CHECKING:
    from .train import Train


class MileageLog(Base):
    """Daily mileage log"""
    __tablename__ = "mileage_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    train_id: Mapped[str] = mapped_column(
        Text, ForeignKey("trains.train_id", ondelete="CASCADE"), nullable=False, index=True
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    km_run: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)

    # Relationships
    train: Mapped["Train"] = relationship(back_populates="mileage_logs")


class MileageLogSchema(BaseSchema):
    """Mileage log response"""
    id: int
    train_id: str
    log_date: date
    km_run: float
