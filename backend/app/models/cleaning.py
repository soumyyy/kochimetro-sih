"""
Cleaning slots models and schemas
"""
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Integer, Text, Numeric, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .depot import StablingBay


class CleaningSlot(Base):
    """Cleaning slot model"""
    __tablename__ = "cleaning_slots"

    slot_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    bay_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("stabling_bays.bay_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    start_ts: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    end_ts: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    manpower: Mapped[int] = mapped_column(Integer, nullable=False)
    clean_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    bay: Mapped["StablingBay"] = relationship()


# Pydantic schemas
class CleaningSlotSchema(BaseSchema):
    """Cleaning slot response schema"""
    slot_id: str
    bay_id: str
    start_ts: datetime
    end_ts: datetime
    manpower: int
    clean_type: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class CleaningSlotCreateSchema(BaseCreateSchema):
    """Cleaning slot creation schema"""
    bay_id: str
    start_ts: datetime
    end_ts: datetime
    manpower: int
    clean_type: str


class CleaningSlotUpdateSchema(BaseUpdateSchema):
    """Cleaning slot update schema"""
    start_ts: Optional[datetime] = None
    end_ts: Optional[datetime] = None
    manpower: Optional[int] = None
    clean_type: Optional[str] = None
