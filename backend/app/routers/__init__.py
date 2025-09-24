"""
API routers package
"""
from fastapi import APIRouter
from app.routers import (
    ingest,
    plans,
    reference,
    branding,
    mileage,
    alerts
)

api_router = APIRouter()

# Include all routers
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(reference.router, prefix="/ref", tags=["reference"])
api_router.include_router(branding.router, prefix="/branding", tags=["branding"])
api_router.include_router(mileage.router, prefix="/mileage", tags=["mileage"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
