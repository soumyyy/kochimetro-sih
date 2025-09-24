"""
Cleaning slots models aligned with Supabase schema
"""
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .depot import StablingBay


class CleaningSlot(Base):
    """Cleaning slot schedule"""
    __tablename__ = "cleaning_slots"

    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    bay_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stabling_bays.bay_id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    manpower: Mapped[int] = mapped_column(Integer, nullable=False)
    clean_type: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    bay: Mapped["StablingBay"] = relationship()


# Pydantic schemas
class CleaningSlotSchema(BaseSchema):
    """Cleaning slot response schema"""
    slot_id: uuid.UUID
    bay_id: uuid.UUID
    start_ts: datetime
    end_ts: datetime
    manpower: int
    clean_type: str


class CleaningSlotCreateSchema(BaseCreateSchema):
    """Cleaning slot creation schema"""
    bay_id: uuid.UUID
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
