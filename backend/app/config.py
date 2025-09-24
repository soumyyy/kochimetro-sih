"""
Application configuration
"""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Database (Supabase)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:YOUR_SUPABASE_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres"

    # Application
    APP_NAME: str = "Kochi Metro IBL Planner"
    APP_VERSION: str = "1.0.0"
    APP_TIMEZONE: str = "Asia/Kolkata"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # Optimization parameters
    ACTIVE_MIN: int = 7
    ACTIVE_MAX: int = 9
    SERVICE_HOURS: float = 16.5
    NIGHT_START_HOUR: int = 21
    NIGHT_END_HOUR: int = 5

    # Default weights
    W_RISK: float = 1.0
    W_BRAND: float = 0.6
    W_MILEAGE: float = 0.2
    W_CLEAN: float = 0.4
    W_SHUNT: float = 0.15
    W_OVERRIDE: float = 3.0

    # Time step for IBL scheduling (minutes)
    IBL_TIME_STEP_MIN: int = 10

    # Standby minimum reserve
    STANDBY_MIN: int = 1

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
