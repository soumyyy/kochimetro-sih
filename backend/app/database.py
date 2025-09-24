"""
Database configuration and session management
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Create async engine with environment-specific settings
def create_engine():
    """Create database engine with appropriate settings for environment"""
    engine_config = {
        "echo": settings.is_development(),  # SQL debugging in dev only
        "future": True,
        "pool_size": 20 if settings.is_production() else 10,
        "max_overflow": 30 if settings.is_production() else 20,
    }

    if settings.is_production():
        # Production optimizations
        engine_config.update({
            "pool_pre_ping": True,  # Validate connections
            "pool_recycle": 3600,   # Recycle connections every hour
        })

    return create_async_engine(settings.DATABASE_URL, **engine_config)

# Create engine instance
engine = create_engine()

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


async def get_db() -> AsyncSession:
    """Dependency for database sessions"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
