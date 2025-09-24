"""
Maintenance and compliance models and schemas
"""
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import date, datetime
from sqlalchemy import String, Integer, Text, Date, JSON, ForeignKey, Boolean, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .train import Train


class Department(Base):
    """Department model for fitness certificates"""
    __tablename__ = "departments"

    dept_code: Mapped[str] = mapped_column(String(10), primary_key=True, index=True)
    dept_name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_safety_critical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    certificates: Mapped[List["FitnessCertificate"]] = relationship(back_populates="department")


class FitnessCertificate(Base):
    """Fitness certificate model"""
    __tablename__ = "fitness_certificates"

    cert_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    train_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("trains.train_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dept: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("departments.dept_code", ondelete="CASCADE"),
        nullable=False
    )
    valid_from: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    valid_to: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    source_ref: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    train: Mapped["Train"] = relationship(back_populates="fitness_certificates")
    department: Mapped["Department"] = relationship(back_populates="certificates")


class JobCard(Base):
    """Job card model for maintenance work orders"""
    __tablename__ = "job_cards"

    job_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    train_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("trains.train_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="Maximo")
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ibl_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    train: Mapped["Train"] = relationship(back_populates="job_cards")


# Pydantic schemas
class DepartmentSchema(BaseSchema):
    """Department response schema"""
    dept_code: str
    dept_name: str
    description: Optional[str]
    is_safety_critical: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class FitnessCertificateSchema(BaseSchema):
    """Fitness certificate response schema"""
    cert_id: str
    train_id: str
    dept_code: str
    certificate_number: str
    valid_from: date
    valid_to: date
    issued_by: Optional[str]
    status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class JobCardSchema(BaseSchema):
    """Job card response schema"""
    job_id: str
    source_system: str
    train_id: str
    job_type: str
    description: str
    status: str
    priority: str
    safety_critical: bool
    estimated_duration_hours: Optional[float]
    due_date: Optional[datetime]
    planned_start: Optional[datetime]
    actual_start: Optional[datetime]
    completed_at: Optional[datetime]
    assigned_crew: Optional[str]
    work_center: Optional[str]
    material_requirements: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
