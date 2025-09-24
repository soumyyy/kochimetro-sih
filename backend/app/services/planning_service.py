"""
Planning Service
Main orchestrator for the induction planning system
"""
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from .feature_extraction import FeatureExtractionService
from .optimization import OptimizationService
from .fleet_service import FleetService
from ..models import (
    InductionPlan,
    InductionPlanItem,
    BayOccupancy,
    Alert,
)


class PlanningService:
    """Main service for orchestrating the planning system"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.feature_service = FeatureExtractionService(db_session)
        self.optimization_service = OptimizationService(db_session)
        self.fleet_service = FleetService(db_session)

    async def create_plan(
        self,
        plan_date: date,
        weights: Optional[Dict] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Create a new induction plan"""
        if plan_date <= date.today():
            raise ValueError("Plan date must be in the future")

        existing_plan = await self.db.execute(
            select(InductionPlan).where(InductionPlan.plan_date == plan_date)
        )
        if existing_plan.scalar_one_or_none():
            raise ValueError(f"Plan for {plan_date} already exists")

        plan = InductionPlan(
            plan_date=plan_date,
            status="draft",
            notes=notes,
            weights_json=weights or {
                "w_risk": 1.0,
                "w_brand": 0.6,
                "w_mileage": 0.2,
                "w_clean": 0.4,
                "w_shunt": 0.15,
                "w_override": 3.0,
            },
        )

        self.db.add(plan)
        await self.db.flush()
        await self.db.commit()

        return str(plan.plan_id)

    async def run_plan_optimization(self, plan_id: str, weights: Optional[Dict] = None) -> Dict[str, Any]:
        """Run optimization for an existing plan"""
        plan_uuid = self._parse_plan_id(plan_id)
        plan = await self.db.get(InductionPlan, plan_uuid)

        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        if plan.status == "finalized":
            raise ValueError(f"Plan {plan_id} is already finalized")

        plan.status = "running"
        await self.db.commit()

        try:
            result = await self.optimization_service.run_optimization(plan, weights)

            plan.status = "completed"
            await self.db.commit()

            return {
                "plan_id": str(plan.plan_id),
                "summary": result.summary,
                "items": result.items,
                "ibl_gantt": result.ibl_gantt,
                "turnout_plan": result.turnout_plan,
                "alerts": result.alerts,
                "execution_time": result.execution_time,
            }

        except Exception as exc:
            await self.db.execute(
                update(InductionPlan)
                .where(InductionPlan.plan_id == plan_uuid)
                .set({"status": "failed"})
            )
            await self.db.commit()
            raise exc

    async def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get plan details and results"""
        plan_uuid = self._parse_plan_id(plan_id)
        plan = await self.db.get(InductionPlan, plan_uuid)
        if not plan:
            return None

        items_result = await self.db.execute(
            select(InductionPlanItem).where(InductionPlanItem.plan_id == plan_uuid)
        )
        items = items_result.scalars().all()

        occupancy_result = await self.db.execute(
            select(BayOccupancy)
            .where(BayOccupancy.from_ts >= datetime.combine(plan.plan_date, datetime.min.time()))
            .where(
                BayOccupancy.from_ts
                < datetime.combine(plan.plan_date + timedelta(days=1), datetime.min.time())
            )
        )
        occupancies = occupancy_result.scalars().all()

        alerts_result = await self.db.execute(select(Alert).where(Alert.plan_id == plan_uuid))
        alerts = alerts_result.scalars().all()

        return {
            "plan_id": str(plan.plan_id),
            "plan_date": plan.plan_date,
            "status": plan.status,
            "weights": plan.weights_json,
            "created_by": plan.created_by,
            "notes": plan.notes,
            "items": [
                {
                    "item_id": item.item_id,
                    "train_id": item.train_id,
                    "decision": item.decision,
                    "bay_id": item.bay_id,
                    "turnout_rank": item.turnout_rank,
                    "km_target": float(item.km_target) if item.km_target is not None else None,
                    "notes": item.notes,
                    "explain": item.explain_json,
                }
                for item in items
            ],
            "ibl_gantt": [
                {
                    "bay_id": occ.bay_id,
                    "train_id": occ.train_id,
                    "from_ts": occ.from_ts.isoformat(),
                    "to_ts": occ.to_ts.isoformat(),
                }
                for occ in occupancies
            ],
            "alerts": [
                {
                    "alert_id": alert.alert_id,
                    "severity": alert.severity,
                    "message": alert.message,
                    "data": alert.data,
                    "resolved": alert.resolved,
                    "created_at": alert.created_at.isoformat(),
                }
                for alert in alerts
            ],
        }

    async def get_fleet_status(self) -> Dict[str, Any]:
        """Get current fleet status overview"""
        return await self.fleet_service.get_fleet_overview()

    async def get_train_features(self, train_id: str, plan_date: date) -> Optional[Dict[str, Any]]:
        """Get detailed features for a specific train"""
        features = await self.feature_service.extract_features(plan_date, [train_id])
        feature = features.get(train_id)
        if not feature:
            return None

        return {
            "train_id": feature.train_id,
            "fitness_ok": feature.fit_ok,
            "fit_expiry_buffer_hours": feature.fit_expiry_buffer_hours,
            "wo_blocking": feature.wo_blocking,
            "critical_wo_count": feature.critical_wo_count,
            "total_wo_count": feature.total_wo_count,
            "active_campaign": feature.active_campaign,
            "brand_target_h": feature.brand_target_h,
            "brand_rolling_deficit_h": feature.brand_rolling_deficit_h,
            "km_cum": feature.km_cum,
            "expected_km_if_active": feature.expected_km_if_active,
            "mileage_dev": feature.mileage_dev,
            "needs_clean": feature.needs_clean,
            "clean_type": feature.clean_type,
            "clean_duration_min": feature.clean_duration_min,
            "skill_need": feature.skill_need,
            "current_bay": feature.current_bay,
            "exit_time_cost_hint_sec": feature.exit_time_cost_hint_sec,
            "explanation": feature.explanation,
        }

    async def finalize_plan(self, plan_id: str) -> bool:
        """Finalize a completed plan (lock for execution)"""
        plan_uuid = self._parse_plan_id(plan_id)
        plan = await self.db.get(InductionPlan, plan_uuid)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        if plan.status != "completed":
            raise ValueError(f"Plan {plan_id} must be completed before finalization")

        plan.status = "finalized"
        await self.db.commit()
        return True

    async def get_plans_list(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get list of plans with pagination"""
        result = await self.db.execute(
            select(InductionPlan)
            .order_by(InductionPlan.plan_date.desc())
            .limit(limit)
            .offset(offset)
        )
        plans = result.scalars().all()

        return [
            {
                "plan_id": str(plan.plan_id),
                "plan_date": plan.plan_date,
                "created_by": plan.created_by,
                "status": plan.status,
                "weights_json": plan.weights_json,
                "notes": plan.notes,
            }
            for plan in plans
        ]

    async def get_plan_summary(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get summary statistics for a plan"""
        plan_data = await self.get_plan(plan_id)
        if not plan_data:
            return None

        items = plan_data["items"]
        active_count = sum(1 for item in items if item["decision"] == "active")
        standby_count = sum(1 for item in items if item["decision"] == "standby")
        ibl_count = sum(1 for item in items if item["decision"] == "ibl")

        return {
            "plan_id": plan_data["plan_id"],
            "plan_date": plan_data["plan_date"],
            "status": plan_data["status"],
            "active_count": active_count,
            "standby_count": standby_count,
            "ibl_count": ibl_count,
            "total_trains": len(items),
        }

    def _parse_plan_id(self, plan_id: str) -> uuid.UUID:
        """Convert incoming plan id to UUID"""
        if isinstance(plan_id, uuid.UUID):
            return plan_id
        try:
            return uuid.UUID(str(plan_id))
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid plan id {plan_id}") from exc
