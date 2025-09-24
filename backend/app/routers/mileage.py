"""
Mileage analytics endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()


@router.get("/variance", summary="Get mileage variance")
async def get_mileage_variance(
    window: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get fleet mileage variance analysis"""
    # TODO: Implement mileage variance calculation
    return {"variance_analysis": {}}
