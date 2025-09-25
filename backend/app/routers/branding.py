"""Branding analytics endpoints."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import BrandingService

router = APIRouter()


@router.post("/rollup/run", summary="Run exposure rollup")
async def run_rollup(
    rollup_date: Optional[date] = Query(None, description="Anchor date for the rollup window"),
    window: int = Query(14, ge=1, le=90, description="Number of days summarised in the rollup"),
    db: AsyncSession = Depends(get_db),
):
    """Run the branding exposure rollup and return the latest snapshot."""
    service = BrandingService(db)
    summary = await service.get_rollup(window=window, end_date=rollup_date)
    return {"message": "Rollup completed", "summary": summary}


@router.get("/rollup", summary="Get exposure analytics")
async def get_exposure_analytics(
    rollup_date: Optional[date] = Query(None, description="Anchor date for the rollup window"),
    window: int = Query(14, ge=1, le=90, description="Number of days summarised in the rollup"),
    db: AsyncSession = Depends(get_db),
):
    """Return campaign exposure analytics for sponsors and wraps."""
    service = BrandingService(db)
    return await service.get_rollup(window=window, end_date=rollup_date)
