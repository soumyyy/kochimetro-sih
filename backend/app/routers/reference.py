"""
Reference data endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database import get_db

router = APIRouter()


@router.get("/depot", summary="Get depot information")
async def get_depot_info(db: AsyncSession = Depends(get_db)):
    """Get depot, bays, routes, and conflicts information"""
    # TODO: Implement depot data retrieval
    return {"depots": [], "bays": [], "routes": [], "conflicts": []}


@router.get("/trains", summary="Get train roster")
async def get_trains(db: AsyncSession = Depends(get_db)):
    """Get train roster with feature snapshot"""
    # TODO: Implement train roster retrieval
    return {"trains": []}


@router.get("/sponsors", summary="Get sponsor information")
async def get_sponsors(db: AsyncSession = Depends(get_db)):
    """Get sponsor and campaign information"""
    # TODO: Implement sponsor data retrieval
    return {"sponsors": [], "campaigns": []}
