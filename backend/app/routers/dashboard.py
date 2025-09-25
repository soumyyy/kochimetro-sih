"""Dashboard summary endpoints with lightweight caching."""
import asyncio
import time
from datetime import date
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import PlanningService, FleetService

CACHE_TTL_SECONDS = 30
_CACHE: Dict[Tuple[str, bool], Tuple[float, Dict[str, Any]]] = {}
_CACHE_LOCK = asyncio.Lock()

router = APIRouter()


def _cache_key(plan_date: Optional[date], include_details: bool) -> Tuple[str, bool]:
    key = plan_date.isoformat() if plan_date else "latest"
    return (key, include_details)


async def _build_dashboard_summary(
    session: AsyncSession,
    plan_date: Optional[date],
    include_details: bool,
) -> Dict[str, Any]:
    planning_service = PlanningService(session)
    fleet_service = FleetService(session)

    plan_snapshot = await planning_service.get_plan_snapshot(plan_date)
    if not plan_snapshot:
        raise HTTPException(status_code=404, detail="No plans found")

    plan_details = None
    if include_details:
        plan_details = await planning_service.get_plan_details(plan_date=plan_date, include_features=False)

    recent_plans = await planning_service.get_recent_plans(limit=4)
    recent_alerts = await planning_service.get_recent_alerts(limit=6)
    plan_range = await planning_service.get_plan_date_range()

    fleet_overview = await fleet_service.get_fleet_overview()
    branding = await fleet_service.get_branding_performance(days=14)
    maintenance = await fleet_service.get_maintenance_backlog()

    return {
        "latest_plan": plan_snapshot,
        "plan_details": plan_details,
        "recent_plans": recent_plans,
        "alerts": recent_alerts,
        "fleet": fleet_overview,
        "branding": branding,
        "maintenance": maintenance,
        "data_window": plan_range,
    }


@router.get("/summary", summary="Get dashboard summary")
async def get_dashboard_summary(
    plan_date: Optional[date] = Query(None, description="Plan date (defaults to latest)"),
    include_details: bool = Query(False, description="Include plan details in response"),
    force_refresh: bool = Query(False, description="Bypass in-memory cache"),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregated metrics for the dashboard view with basic caching."""
    key = _cache_key(plan_date, include_details)
    now = time.time()

    if not force_refresh:
        cached = _CACHE.get(key)
        if cached and now - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]

    async with _CACHE_LOCK:
        if not force_refresh:
            cached = _CACHE.get(key)
            if cached and now - cached[0] < CACHE_TTL_SECONDS:
                return cached[1]

        summary = await _build_dashboard_summary(db, plan_date, include_details)
        _CACHE[key] = (time.time(), summary)
        return summary
