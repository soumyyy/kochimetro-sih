"""
Base model classes and common functionality aligned with Supabase schema
"""
from sqlalchemy.orm import DeclarativeBase, declared_attr
from pydantic import BaseModel


class Base(DeclarativeBase):
    """Declarative base for all ORM models"""

    @declared_attr
    def __tablename__(cls) -> str:  # type: ignore[override]
        """Generate snake_case table names by default"""
        return cls.__name__.lower()


# Pydantic base models for API responses
class BaseSchema(BaseModel):
    """Base schema for API responses"""

    class Config:
        from_attributes = True
        populate_by_name = True


class BaseCreateSchema(BaseModel):
    """Base schema for create operations"""


class BaseUpdateSchema(BaseModel):
    """Base schema for update operations"""
