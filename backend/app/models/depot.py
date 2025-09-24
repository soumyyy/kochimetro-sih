"""
Depot infrastructure models and schemas
"""
from typing import Optional, List, TYPE_CHECKING
from datetime import date, datetime
from sqlalchemy import String, Integer, Boolean, Numeric, Text, Time, Date, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .train import Train
    from .plan import TurnoutPlan


class Depot(Base):
    """Depot model"""
    __tablename__ = "depots"

    depot_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    bays: Mapped[List["StablingBay"]] = relationship(back_populates="depot")
    routes: Mapped[List["DepotRoute"]] = relationship(back_populates="depot")


class StablingBay(Base):
    """Stabling bay model"""
    __tablename__ = "stabling_bays"

    bay_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    depot_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("depots.depot_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    position_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    electrified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    length_m: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=100.0)
    access_time_min: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False, default=3.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    depot: Mapped["Depot"] = relationship(back_populates="bays")
    occupancies: Mapped[List["BayOccupancy"]] = relationship(back_populates="bay")


class DepotRoute(Base):
    """Depot route model"""
    __tablename__ = "depot_routes"

    route_id: Mapped[str] = mapped_column(String(10), primary_key=True, index=True)
    depot_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("depots.depot_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    throat_side: Mapped[str] = mapped_column(String(1), nullable=False)
    turnout_speed_kmph: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)
    lock_time_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    depot: Mapped["Depot"] = relationship(back_populates="routes")
    turnout_plans: Mapped[List["TurnoutPlan"]] = relationship(back_populates="route")


class BayOccupancy(Base):
    """Bay occupancy model"""
    __tablename__ = "bay_occupancy"

    occ_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bay_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("stabling_bays.bay_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    train_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("trains.train_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    from_ts: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    to_ts: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    # Relationships
    bay: Mapped["StablingBay"] = relationship(back_populates="occupancies")
    train: Mapped["Train"] = relationship()


# Pydantic schemas
class DepotSchema(BaseSchema):
    """Depot response schema"""
    depot_id: str
    name: str
    location: Optional[str]
    total_bays: int
    operational_hours_start: Optional[str]
    operational_hours_end: Optional[str]
    contact_person: Optional[str]
    phone: Optional[str]
    emergency_contact: Optional[str]
    active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class StablingBaySchema(BaseSchema):
    """Stabling bay response schema"""
    bay_id: str
    depot_id: str
    position_idx: int
    throat_side: str
    has_pit: bool
    washer_accessible: bool
    usable_length_m: float
    access_time_min: int
    maintenance_due: Optional[date]
    status: str
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class DepotRouteSchema(BaseSchema):
    """Depot route response schema"""
    route_id: str
    depot_id: str
    throat_side: str
    turnout_speed_kmph: float
    lock_time_sec: int
    description: Optional[str]
    active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class BayOccupancySchema(BaseSchema):
    """Bay occupancy response schema"""
    occupancy_id: str
    bay_id: str
    train_id: str
    from_ts: datetime
    to_ts: datetime
    job_type: str
    assigned_crew: Optional[str]
    priority: str
    status: str
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
