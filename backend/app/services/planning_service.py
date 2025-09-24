"""
Planning Service
Main orchestrator for the induction planning system
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker

from .feature_extraction import FeatureExtractionService
from .optimization import OptimizationService
from .fleet_service import FleetService
from ..models import (
    InductionPlan, InductionPlanItem, Train,
    StablingBay, BayOccupancy, User
)


class PlanningService:
    """Main service for orchestrating the planning system"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.feature_service = FeatureExtractionService(db_session)
        self.optimization_service = OptimizationService(db_session)
        self.fleet_service = FleetService(db_session)

    async def create_plan(self, plan_date: date, weights: Optional[Dict] = None) -> str:
        """
        Create a new induction plan

        Args:
            plan_date: Date for the plan
            weights: Optional optimization weights override

        Returns:
            plan_id: The created plan ID
        """
        # Validate plan date
        if plan_date <= date.today():
            raise ValueError("Plan date must be in the future")

        # Check if plan already exists
        existing_plan = await self.db.execute(
            select(InductionPlan.plan_id).where(InductionPlan.plan_date == plan_date)
        )
        if existing_plan.scalar_one_or_none():
            raise ValueError(f"Plan for {plan_date} already exists")

        # Create plan ID
        plan_id = f"plan_{plan_date.strftime('%Y%m%d')}"

        # Create plan record
        plan = InductionPlan(
            plan_id=plan_id,
            plan_date=plan_date,
            status="draft",
            weights_json=weights or {
                'w_risk': 1.0,
                'w_brand': 0.6,
                'w_mileage': 0.2,
                'w_clean': 0.4,
                'w_shunt': 0.15,
                'w_override': 3.0
            },
            day_type="weekday" if plan_date.weekday() < 5 else "weekend"
        )

        self.db.add(plan)
        await self.db.commit()

        return plan_id

    async def run_plan_optimization(self, plan_id: str, weights: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Run optimization for an existing plan

        Args:
            plan_id: Plan to optimize
            weights: Optional weight overrides

        Returns:
            Optimization results
        """
        # Get plan
        plan_result = await self.db.execute(
            select(InductionPlan.plan_id).where(InductionPlan.plan_id == plan_id)
        )
        plan = plan_result.scalar_one_or_none()

        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        if plan.status == "finalized":
            raise ValueError(f"Plan {plan_id} is already finalized")

        # Update plan status
        plan.status = "running"
        await self.db.commit()

        try:
            # Run optimization
            result = await self.optimization_service.run_optimization(plan.plan_date, weights)

            # Update plan status
            await self.db.execute(
                update(InductionPlan)
                .where(InductionPlan.plan_id == plan_id)
                .values(status="completed")
            )
            await self.db.commit()

            return {
                'plan_id': result.plan_id,
                'summary': result.summary,
                'items': result.items,
                'ibl_gantt': result.ibl_gantt,
                'turnout_plan': result.turnout_plan,
                'alerts': result.alerts,
                'execution_time': result.execution_time
            }

        except Exception as e:
            # Update plan status to failed
            await self.db.execute(
                update(InductionPlan)
                .where(InductionPlan.plan_id == plan_id)
                .values(status="failed")
            )
            await self.db.commit()
            raise e

    async def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get plan details and results"""
        plan_result = await self.db.execute(
            select(
                InductionPlan.plan_id,
                InductionPlan.plan_date,
                InductionPlan.created_by,
                InductionPlan.status,
                InductionPlan.weights_json,
                InductionPlan.notes
            )
            .where(InductionPlan.plan_id == plan_id)
        )
        plan = plan_result.scalar_one_or_none()

        if not plan:
            return None

        # Get plan items
        items_result = await self.db.execute(
            select(InductionPlanItem)
            .where(InductionPlanItem.plan_id == plan_id)
        )
        items = items_result.scalars().all()

        # Get bay occupancies (IBL schedule)
        occupancy_result = await self.db.execute(
            select(BayOccupancy)
            .where(BayOccupancy.from_ts >= datetime.combine(plan.plan_date, datetime.min.time()))
            .where(BayOccupancy.from_ts < datetime.combine(plan.plan_date + timedelta(days=1), datetime.min.time()))
        )
        occupancies = occupancy_result.scalars().all()

        # Get alerts
        from ..models import Alert
        alerts_result = await self.db.execute(
            select(Alert)
            .where(Alert.plan_id == plan_id)
        )
        alerts = alerts_result.scalars().all()

        return {
            'plan_id': plan.plan_id,
            'plan_date': plan.plan_date,
            'status': plan.status,
            'weights': plan.weights_json,
            'created_by': plan.created_by,
            'notes': plan.notes,
            'items': [
                {
                    'item_id': item.item_id,
                    'train_id': item.train_id,
                    'decision': item.decision,
                    'bay_id': item.bay_id,
                    'turnout_rank': item.turnout_rank,
                    'km_target': item.km_target,
                    'notes': item.notes,
                    'explain': item.explain_json,
                    'manual_override': item.manual_override,
                    'override_reason': item.override_reason
                } for item in items
            ],
            'ibl_gantt': [
                {
                    'bay_id': occ.bay_id,
                    'train_id': occ.train_id,
                    'from_ts': occ.from_ts.isoformat(),
                    'to_ts': occ.to_ts.isoformat(),
                    'job_type': getattr(occ, 'job_type', 'maintenance')
                } for occ in occupancies
            ],
            'alerts': [
                {
                    'alert_id': alert.alert_id,
                    'severity': alert.severity,
                    'message': alert.message,
                    'data': alert.data,
                    'resolved': alert.resolved,
                    'created_at': alert.created_at.isoformat()
                } for alert in alerts
            ]
        }

    async def get_fleet_status(self) -> Dict[str, Any]:
        """Get current fleet status overview"""
        return await self.fleet_service.get_fleet_overview()

    async def get_train_features(self, train_id: str, plan_date: date) -> Optional[Dict[str, Any]]:
        """Get detailed features for a specific train"""
        from .feature_extraction import TrainFeatures

        features = await self.feature_service.extract_features(plan_date, [train_id])

        if train_id not in features:
            return None

        feature = features[train_id]

        return {
            'train_id': feature.train_id,
            'fitness_ok': feature.fit_ok,
            'fit_expiry_buffer_hours': feature.fit_expiry_buffer_hours,
            'wo_blocking': feature.wo_blocking,
            'critical_wo_count': feature.critical_wo_count,
            'total_wo_count': feature.total_wo_count,
            'active_campaign': feature.active_campaign,
            'brand_target_h': feature.brand_target_h,
            'brand_rolling_deficit_h': feature.brand_rolling_deficit_h,
            'km_cum': feature.km_cum,
            'expected_km_if_active': feature.expected_km_if_active,
            'mileage_dev': feature.mileage_dev,
            'needs_clean': feature.needs_clean,
            'clean_type': feature.clean_type,
            'clean_duration_min': feature.clean_duration_min,
            'skill_need': feature.skill_need,
            'current_bay': feature.current_bay,
            'exit_time_cost_hint_sec': feature.exit_time_cost_hint_sec,
            'explanation': feature.explanation
        }

    async def finalize_plan(self, plan_id: str) -> bool:
        """Finalize a completed plan (lock for execution)"""
        # Get plan
        plan_result = await self.db.execute(
            select(InductionPlan.plan_id, InductionPlan.status).where(InductionPlan.plan_id == plan_id)
        )
        plan = plan_result.scalar_one_or_none()

        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        if plan.status != "completed":
            raise ValueError(f"Plan {plan_id} must be completed before finalization")

        if plan.finalized_at:
            raise ValueError(f"Plan {plan_id} is already finalized")

        # Finalize the plan
        from sqlalchemy import update
        await self.db.execute(
            update(InductionPlan)
            .where(InductionPlan.plan_id == plan_id)
            .values(
                status="finalized",
                finalized_at=datetime.now()
            )
        )
        await self.db.commit()

        return True

    async def get_plans_list(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get list of plans with pagination"""
        result = await self.db.execute(
            select(
                InductionPlan.plan_id,
                InductionPlan.plan_date,
                InductionPlan.created_by,
                InductionPlan.status,
                InductionPlan.weights_json,
                InductionPlan.notes
            )
            .order_by(InductionPlan.plan_date.desc())
            .limit(limit)
            .offset(offset)
        )
        plans = result.scalars().all()

        return [
            {
                'plan_id': plan.plan_id,
                'plan_date': plan.plan_date,
                'created_by': plan.created_by,
                'status': plan.status,
                'weights_json': plan.weights_json,
                'notes': plan.notes
            } for plan in plans
        ]

    async def get_plan_summary(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get summary statistics for a plan"""
        plan_data = await self.get_plan(plan_id)
        if not plan_data:
            return None

        items = plan_data['items']
        active_count = sum(1 for item in items if item['decision'] == 'active')
        standby_count = sum(1 for item in items if item['decision'] == 'standby')
        ibl_count = sum(1 for item in items if item['decision'] == 'ibl')

        # Count high-risk active trains
        high_risk_active = 0
        for item in items:
            if item['decision'] == 'active':
                # Check if train has fitness issues or critical WOs
                features = await self.get_train_features(item['train_id'], plan_data['plan_date'])
                if features and (not features['fitness_ok'] or features['critical_wo_count'] > 0):
                    high_risk_active += 1

        return {
            'plan_id': plan_id,
            'plan_date': plan_data['plan_date'],
            'status': plan_data['status'],
            'active_trains': active_count,
            'standby_trains': standby_count,
            'ibl_trains': ibl_count,
            'high_risk_active': high_risk_active,
            'alerts_count': len(plan_data['alerts']),
            'ibl_jobs_count': len(plan_data['ibl_gantt'])
        }
