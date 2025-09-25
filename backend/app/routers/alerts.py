"""
Alert management endpoints
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import PlanningService

router = APIRouter()


@router.get("/", summary="Get alerts")
async def get_alerts(
    resolved: Optional[bool] = Query(None, description="Filter by resolution state"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum alerts to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get alerts and notifications"""
    planning_service = PlanningService(db)
    alerts = await planning_service.list_alerts(resolved=resolved, limit=limit)
    return {"alerts": alerts}


@router.post("/{alert_id}/resolve", summary="Resolve alert")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Resolve an alert"""
    planning_service = PlanningService(db)
    try:
        alert = await planning_service.resolve_alert(alert_id)
        return {"message": "Alert resolved", "alert": alert}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
