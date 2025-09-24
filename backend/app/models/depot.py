"""
Depot and bay models matching Supabase schema
"""
import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Integer, Boolean, Numeric, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .train import Train


class Depot(Base):
    """Depot master"""
    __tablename__ = "depots"

    depot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[Optional[str]] = mapped_column(Text, nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    bays: Mapped[List["StablingBay"]] = relationship(back_populates="depot")


class StablingBay(Base):
    """Stabling bay inventory"""
    __tablename__ = "stabling_bays"

    bay_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    depot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("depots.depot_id", ondelete="CASCADE"), nullable=False, index=True
    )
    position_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    electrified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    length_m: Mapped[float] = mapped_column(Numeric, nullable=False, default=100.0)
    access_time_min: Mapped[float] = mapped_column(Numeric, nullable=False, default=3.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    depot: Mapped["Depot"] = relationship(back_populates="bays")
    occupancies: Mapped[List["BayOccupancy"]] = relationship(back_populates="bay")
    trains: Mapped[List["Train"]] = relationship(back_populates="bay")


class BayOccupancy(Base):
    """Night bay occupancy slots"""
    __tablename__ = "bay_occupancy"

    occ_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bay_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stabling_bays.bay_id", ondelete="CASCADE"), nullable=False, index=True
    )
    train_id: Mapped[str] = mapped_column(
        Text, ForeignKey("trains.train_id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    to_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    bay: Mapped["StablingBay"] = relationship(back_populates="occupancies")
    train: Mapped["Train"] = relationship(back_populates="bay_occupancies")


# Pydantic schemas
class DepotSchema(BaseSchema):
    """Depot response schema"""
    depot_id: uuid.UUID
    name: str
    code: Optional[str]
    is_active: bool


class StablingBaySchema(BaseSchema):
    """Stabling bay response schema"""
    bay_id: uuid.UUID
    depot_id: uuid.UUID
    position_idx: int
    electrified: bool
    length_m: float
    access_time_min: float
    is_active: bool


class BayOccupancySchema(BaseSchema):
    """Bay occupancy response schema"""
    occ_id: int
    bay_id: uuid.UUID
    train_id: str
    from_ts: datetime
    to_ts: datetime
