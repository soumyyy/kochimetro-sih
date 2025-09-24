"""
Base model classes and common functionality
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import TIMESTAMP, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from pydantic import BaseModel


class Base(DeclarativeBase):
    """Base class for all database models"""

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name"""
        return cls.__name__.lower()

    created_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# Pydantic base models for API responses
class BaseSchema(BaseModel):
    """Base schema for API responses"""
    class Config:
        from_attributes = True
        populate_by_name = True


class BaseCreateSchema(BaseModel):
    """Base schema for create operations"""
    pass


class BaseUpdateSchema(BaseModel):
    """Base schema for update operations"""
    pass
