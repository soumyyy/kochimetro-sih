"""
User models and schemas aligned with Supabase
"""
import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseSchema, BaseCreateSchema, BaseUpdateSchema

if TYPE_CHECKING:
    from .plan import InductionPlan
    from .system import Override


class User(Base):
    """Supabase-backed user"""
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="viewer")

    # Relationships
    created_plans: Mapped[List["InductionPlan"]] = relationship(back_populates="creator")
    overrides: Mapped[List["Override"]] = relationship(back_populates="user")


# Pydantic schemas
class UserSchema(BaseSchema):
    """User response schema"""
    user_id: uuid.UUID
    username: str
    display_name: Optional[str]
    role: str


class UserCreateSchema(BaseCreateSchema):
    """User creation schema"""
    username: str
    display_name: Optional[str] = None
    role: str = "viewer"


class UserUpdateSchema(BaseUpdateSchema):
    """User update schema"""
    display_name: Optional[str] = None
    role: Optional[str] = None
