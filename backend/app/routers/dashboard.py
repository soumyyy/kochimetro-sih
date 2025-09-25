"""Dashboard summary endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import PlanningService, FleetService

router = APIRouter()


@router.get("/summary", summary="Get dashboard summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Return aggregated metrics for the dashboard view"""
    planning_service = PlanningService(db)
    fleet_service = FleetService(db)

    latest_plan = await planning_service.get_latest_plan_snapshot()
    plan_details = await planning_service.get_latest_plan_details()
    recent_plans = await planning_service.get_recent_plans(limit=4)
    recent_alerts = await planning_service.get_recent_alerts(limit=6)
    plan_range = await planning_service.get_plan_date_range()

    fleet_overview = await fleet_service.get_fleet_overview()
    branding = await fleet_service.get_branding_performance(days=14)
    maintenance = await fleet_service.get_maintenance_backlog()

    if not latest_plan:
        raise HTTPException(status_code=404, detail="No plans found")

    return {
        "latest_plan": latest_plan,
        "plan_details": plan_details,
        "recent_plans": recent_plans,
        "alerts": recent_alerts,
        "fleet": fleet_overview,
        "branding": branding,
        "maintenance": maintenance,
        "data_window": plan_range,
    }
