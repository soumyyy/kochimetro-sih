"""
Application configuration
Consolidated configuration with environment support
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # =====================================================
    # DATABASE CONFIGURATION
    # =====================================================

    # Supabase connection string - UPDATE THIS WITH YOUR ACTUAL VALUES
    SUPABASE_URL: str = "https://rpnbdoamiobuxazedaoe.supabase.co"
    SUPABASE_ANON_KEY: str = "your_anon_key_here"
    SUPABASE_SERVICE_ROLE_KEY: str = "your_service_role_key_here"

    # Database connection - use asyncpg for async operations
    DATABASE_URL: str = "postgresql+asyncpg://postgres:hexalith123@db.rpnbdoamiobuxazedaoe.supabase.co:5432/postgres"

    # =====================================================
    # APPLICATION SETTINGS
    # =====================================================

    APP_NAME: str = "Kochi Metro IBL Planner"
    APP_VERSION: str = "1.0.0"
    APP_TIMEZONE: str = "Asia/Kolkata"
    ENVIRONMENT: str = "development"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # =====================================================
    # OPTIMIZATION PARAMETERS
    # =====================================================

    # Fleet constraints
    ACTIVE_MIN: int = 7
    ACTIVE_MAX: int = 9
    STANDBY_MIN: int = 1

    # Service schedule
    SERVICE_HOURS: float = 16.5
    NIGHT_START_HOUR: int = 21
    NIGHT_END_HOUR: int = 5
    IBL_TIME_STEP_MIN: int = 10

    # =====================================================
    # OPTIMIZATION WEIGHTS
    # =====================================================

    W_RISK: float = 1.0      # Safety and reliability
    W_BRAND: float = 0.6     # Branding commitments
    W_MILEAGE: float = 0.2   # Fleet balancing
    W_CLEAN: float = 0.4     # Maintenance scheduling
    W_SHUNT: float = 0.15    # Operational efficiency
    W_OVERRIDE: float = 3.0  # Manual override penalty

    # =====================================================
    # FILE PATHS
    # =====================================================

    DATA_DIR: str = "data"
    CSV_UPLOAD_DIR: str = "data/input"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set environment from env var or default
        self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == 'production'

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == 'development'

    def get_log_level(self) -> str:
        """Get appropriate log level for environment"""
        return "INFO" if self.is_production() else "DEBUG"


# Create global settings instance
settings = Settings()

# =====================================================
# DEPRECATED - Use settings object instead
# =====================================================

# Legacy support - these will be removed in future versions
DATABASE_URL = settings.DATABASE_URL
APP_NAME = settings.APP_NAME
APP_VERSION = settings.APP_VERSION
APP_TIMEZONE = settings.APP_TIMEZONE
CORS_ORIGINS = settings.CORS_ORIGINS
