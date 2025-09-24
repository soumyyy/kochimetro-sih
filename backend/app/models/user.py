"""
User models and schemas
"""
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .plan import InductionPlan, Override


class User(Base):
    """User model"""
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="viewer")

    # Relationships
    created_plans: Mapped[List["InductionPlan"]] = relationship(back_populates="creator")
    overrides: Mapped[List["Override"]] = relationship(back_populates="user")


# Pydantic schemas
class UserSchema(BaseSchema):
    """User response schema"""
    user_id: str
    username: str
    display_name: Optional[str]
    role: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class UserCreateSchema(BaseCreateSchema):
    """User creation schema"""
    username: str
    display_name: Optional[str] = None
    role: str = "viewer"


class UserUpdateSchema(BaseUpdateSchema):
    """User update schema"""
    display_name: Optional[str] = None
    role: Optional[str] = None
