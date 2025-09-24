"""
Maintenance and compliance models aligned with Supabase schema
"""
import uuid
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Text, Boolean, Integer, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .train import Train


class FitnessCertificate(Base):
    """Fitness certificate records"""
    __tablename__ = "fitness_certificates"

    cert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    train_id: Mapped[str] = mapped_column(
        Text, ForeignKey("trains.train_id", ondelete="CASCADE"), nullable=False, index=True
    )
    dept: Mapped[str] = mapped_column(Text, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(nullable=False)
    valid_to: Mapped[datetime] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    source_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    train: Mapped["Train"] = relationship(back_populates="fitness_certificates")


class JobCard(Base):
    """Maintenance job cards"""
    __tablename__ = "job_cards"

    job_id: Mapped[str] = mapped_column(Text, primary_key=True)
    train_id: Mapped[str] = mapped_column(
        Text, ForeignKey("trains.train_id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(Text, nullable=False, default="Maximo")
    status: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ibl_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    train: Mapped["Train"] = relationship(back_populates="job_cards")


# Pydantic schemas
class FitnessCertificateSchema(BaseSchema):
    """Fitness certificate response schema"""
    cert_id: uuid.UUID
    train_id: str
    dept: str
    valid_from: datetime
    valid_to: datetime
    status: str
    source_ref: Optional[str]


class JobCardSchema(BaseSchema):
    """Job card response schema"""
    job_id: str
    train_id: str
    source: str
    status: str
    priority: Optional[int]
    due_date: Optional[date]
    ibl_required: bool
    title: Optional[str]
    details: Optional[str]
