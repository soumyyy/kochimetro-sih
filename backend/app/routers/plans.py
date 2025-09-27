"""
Planning and optimization endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import date
from uuid import UUID

from app.database import get_db
from app.services import PlanningService
router = APIRouter()


class PlanCreate(BaseModel):
    """Plan creation request"""
    plan_date: date
    weights: Optional[Dict[str, float]] = None
    notes: Optional[str] = None


class PlanOverrideRequest(BaseModel):
    """Manual override payload"""
    decision: Optional[str] = None
    bay_id: Optional[str] = None
    turnout_rank: Optional[int] = None
    notes: Optional[str] = None
    reason: str


class WhatIfRequest(BaseModel):
    """What-if analysis request"""
    force: Optional[Any] = None
    ban: Optional[Any] = None
    weight_deltas: Optional[Dict[str, float]] = None


@router.post("/", summary="Create new plan")
async def create_plan(
    plan_data: PlanCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new induction plan"""
    planning_service = PlanningService(db)
    try:
        plan_id = await planning_service.create_plan(
            plan_date=plan_data.plan_date,
            weights=plan_data.weights,
            notes=plan_data.notes,
        )
        return {"plan_id": plan_id, "message": "Plan created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/latest", summary="Get latest plan with details")
async def get_latest_plan_details(
    plan_date: Optional[date] = Query(None, description="Plan date to fetch (defaults to latest)"),
    include_features: bool = Query(True, description="Include per-train feature data"),
    db: AsyncSession = Depends(get_db),
):
    """Return plan details (latest by default)"""
    planning_service = PlanningService(db)
    plan_details = await planning_service.get_plan_details(plan_date=plan_date, include_features=include_features)
    if not plan_details:
        raise HTTPException(status_code=404, detail="No plans found")
    return plan_details


@router.post("/{plan_id}/run", summary="Execute optimization")
async def run_plan(
    plan_id: UUID,
    weight_overrides: Optional[Dict[str, float]] = None,
    db: AsyncSession = Depends(get_db)
):
    """Execute the 3-stage optimization for a plan"""
    planning_service = PlanningService(db)
    try:
        result = await planning_service.run_plan_optimization(
            plan_id=str(plan_id),
            weights=weight_overrides
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/list", summary="List plans")
async def list_plans(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get list of plans with pagination"""
    planning_service = PlanningService(db)
    plans = await planning_service.get_plans_list(limit, offset)
    return {"plans": plans}


@router.patch("/{plan_id}/items/{train_id}", summary="Manual override")
async def override_plan_item(
    plan_id: UUID,
    train_id: str,
    override: PlanOverrideRequest,
    db: AsyncSession = Depends(get_db)
):
    """Manually override a train assignment"""
    planning_service = PlanningService(db)
    payload = override.dict(exclude_unset=True)

    if "decision" in payload and payload["decision"]:
        payload["decision"] = payload["decision"].lower()

    try:
        result = await planning_service.apply_override(str(plan_id), train_id, payload)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{plan_id}/explain/{train_id}", summary="Get explanation")
async def get_explanation(
    plan_id: UUID,
    train_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get decision explanation for a specific train"""
    planning_service = PlanningService(db)
    explanation = await planning_service.get_item_explanation(str(plan_id), train_id)
    if not explanation:
        raise HTTPException(status_code=404, detail="Plan item not found")
    return explanation


@router.get("/{plan_id}", summary="Get plan details")
async def get_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed plan information"""
    planning_service = PlanningService(db)
    plan_data = await planning_service.get_plan(str(plan_id))
    if not plan_data:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan_data


@router.get("/{plan_id}/summary", summary="Get plan summary")
async def get_plan_summary(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get summary statistics for a plan"""
    planning_service = PlanningService(db)
    summary = await planning_service.get_plan_summary(str(plan_id))
    if not summary:
        raise HTTPException(status_code=404, detail="Plan not found")
    return summary


@router.post("/{plan_id}/finalize", summary="Finalize plan")
async def finalize_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Finalize and lock the plan"""
    planning_service = PlanningService(db)
    try:
        success = await planning_service.finalize_plan(str(plan_id))
        return {"message": "Plan finalized successfully", "success": success}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fleet/status", summary="Get fleet status")
async def get_fleet_status(
    db: AsyncSession = Depends(get_db)
):
    """Get current fleet status overview"""
    planning_service = PlanningService(db)
    status = await planning_service.get_fleet_status()
    return status


@router.get("/features/{train_id}", summary="Get train features")
async def get_train_features(
    train_id: str,
    plan_date: date,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed features for a specific train"""
    planning_service = PlanningService(db)
    features = await planning_service.get_train_features(train_id, plan_date)
    if not features:
        raise HTTPException(status_code=404, detail="Train not found")
    return features


@router.post("/{plan_id}/whatif", summary="What-if analysis")
async def whatif_analysis(
    plan_id: UUID,
    whatif_data: WhatIfRequest,
    db: AsyncSession = Depends(get_db)
):
    """Perform what-if analysis without persisting"""
    planning_service = PlanningService(db)
    try:
        scenario = await planning_service.run_what_if(str(plan_id), whatif_data.dict(exclude_unset=True))
        return scenario
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
