"""
Optimization Service
Implements the 3-stage mathematical optimization for train assignment
"""
import uuid
from datetime import datetime, date, time, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ortools.sat.python import cp_model
from ..models import Train, InductionPlan, InductionPlanItem, StablingBay, BayOccupancy
from ..config import settings
from .feature_extraction import FeatureExtractionService, TrainFeatures


@dataclass
class OptimizationResult:
    """Result from optimization run"""
    plan_id: str
    summary: Dict[str, Any]
    items: List[Dict[str, Any]]
    ibl_gantt: List[Dict[str, Any]]
    turnout_plan: List[Dict[str, Any]]
    alerts: List[str]
    execution_time: float
    objective_value: float


class OptimizationService:
    """3-stage optimization service for train fleet management"""

    def __init__(self, db_session):
        self.db = db_session
        self.feature_service = FeatureExtractionService(db_session)
        self.service_start = time(6, 0)  # 06:00
        self.service_end = time(22, 30)  # 22:30
        self.night_start = time(21, 0)  # 21:00
        self.night_end = time(5, 30)   # 05:30

        # Optimization weights (from config)
        self.default_weights = {
            "risk": settings.W_RISK,
            "brand": settings.W_BRAND,
            "mileage": settings.W_MILEAGE,
            "clean": settings.W_CLEAN,
            "shunt": settings.W_SHUNT,
            "override": settings.W_OVERRIDE,
        }
        self.weights = self.default_weights.copy()

    async def run_optimization(
        self,
        plan: InductionPlan,
        weights: Optional[Dict] = None,
        persist: bool = True,
    ) -> OptimizationResult:
        """
        Run the complete 3-stage optimization

        Args:
            plan: Plan to optimize
            weights: Optional weight overrides

        Returns:
            OptimizationResult with all decisions
        """
        self.weights = self.default_weights.copy()
        if weights:
            self.weights.update(weights)

        start_time = datetime.now()
        plan_date = plan.plan_date

        # Stage 1: Assignment (Active/Standby/IBL)
        print(f"Running Stage 1: Train Assignment for {plan_date}")
        assignment_result = await self._stage1_assignment(plan_date)

        # Stage 2: IBL Scheduling
        print("Running Stage 2: IBL Scheduling")
        ibl_schedule = await self._stage2_ibl_scheduling(plan_date, assignment_result)

        # Stage 3: Stabling & Turnout
        print("Running Stage 3: Stabling & Turnout")
        stabling_result = await self._stage3_stabling_turnout(plan_date, assignment_result)

        execution_time = (datetime.now() - start_time).total_seconds()

        # Compile results
        result = OptimizationResult(
            plan_id=str(plan.plan_id),
            summary=self._create_summary(assignment_result, ibl_schedule, stabling_result),
            items=assignment_result['decisions'],
            ibl_gantt=ibl_schedule,
            turnout_plan=stabling_result,
            alerts=assignment_result.get('alerts', []),
            execution_time=execution_time,
            objective_value=assignment_result.get('objective_value', 0)
        )

        if persist:
            # Save to database
            await self._save_plan_to_database(plan, result, plan_date)

        return result

    async def _stage1_assignment(self, plan_date: date) -> Dict[str, Any]:
        """
        Stage 1: Assign trains to Active, Standby, or IBL
        Uses CP-SAT for optimal assignment based on features
        """
        # Extract features for all trains
        features = await self.feature_service.extract_features(plan_date)

        model = cp_model.CpModel()

        # Decision variables
        train_vars = {}
        for train_id, feature in features.items():
            # xA_i, xS_i, xM_i (Active, Standby, IBL)
            xA = model.NewBoolVar(f'xA_{train_id}')
            xS = model.NewBoolVar(f'xS_{train_id}')
            xM = model.NewBoolVar(f'xM_{train_id}')

            train_vars[train_id] = {
                'xA': xA, 'xS': xS, 'xM': xM,
                'features': feature
            }

            # Constraint: exactly one assignment
            model.Add(xA + xS + xM == 1)

        # Active count constraints
        active_vars = [vars['xA'] for vars in train_vars.values()]
        model.Add(sum(active_vars) >= settings.ACTIVE_MIN)
        model.Add(sum(active_vars) <= settings.ACTIVE_MAX)

        # Fitness constraints
        for train_id, vars in train_vars.items():
            feature = vars['features']
            # Can only be active if fitness is OK
            model.Add(vars['xA'] <= (1 if feature.fit_ok else 0))

        # WO blocking constraints
        for train_id, vars in train_vars.items():
            feature = vars['features']
            # Can only be active if not blocked by WO
            model.Add(vars['xA'] <= (0 if feature.wo_blocking else 1))

        # Objective function components
        objective_terms = []

        # Risk component (minimize risk for active trains)
        for train_id, vars in train_vars.items():
            feature = vars['features']
            risk_score = self._calculate_risk_score(feature)
            objective_terms.append(self.weights['risk'] * risk_score * vars['xA'])

        # Branding deficit (minimize deficit)
        for train_id, vars in train_vars.items():
            feature = vars['features']
            brand_deficit = feature.brand_rolling_deficit_h
            # Penalty for not meeting branding targets
            s_brand = model.NewIntVar(0, 1000, f's_brand_{train_id}')
            model.Add(s_brand >= feature.brand_target_h - settings.SERVICE_HOURS * vars['xA'])
            objective_terms.append(self.weights['brand'] * s_brand)

        # Mileage balancing
        for train_id, vars in train_vars.items():
            feature = vars['features']
            mileage_dev = feature.mileage_dev
            s_mile_pos = model.NewIntVar(0, 10000, f's_mile_pos_{train_id}')
            s_mile_neg = model.NewIntVar(0, 10000, f's_mile_neg_{train_id}')

            # Linearize absolute value
            model.Add(s_mile_pos - s_mile_neg == mileage_dev + feature.expected_km_if_active * vars['xA'])
            objective_terms.append(self.weights['mileage'] * (s_mile_pos + s_mile_neg))

        # Cleaning penalties
        for train_id, vars in train_vars.items():
            feature = vars['features']
            clean_penalty = 1 if feature.needs_clean else 0
            objective_terms.append(self.weights['clean'] * clean_penalty * (1 - vars['xM']))

        # Shunting costs
        for train_id, vars in train_vars.items():
            feature = vars['features']
            shunt_cost = feature.exit_time_cost_hint_sec / 60  # Convert to minutes
            objective_terms.append(self.weights['shunt'] * shunt_cost * vars['xA'])

        # Set objective
        model.Minimize(sum(objective_terms))

        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30  # 30 second time limit
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            # Extract results
            decisions = []
            objective_value = solver.ObjectiveValue()

            for train_id, vars in train_vars.items():
                feature = vars['features']

                # Determine assignment
                xA_val = solver.Value(vars['xA'])
                xS_val = solver.Value(vars['xS'])
                xM_val = solver.Value(vars['xM'])

                if xA_val > 0.5:
                    decision = "active"
                    bay_id = None  # Will be assigned in stage 3
                    turnout_rank = None  # Will be assigned in stage 3
                elif xS_val > 0.5:
                    decision = "standby"
                    bay_id = feature.current_bay
                    turnout_rank = None
                else:
                    decision = "ibl"
                    bay_id = None  # Will be assigned in stage 2
                    turnout_rank = None

                decisions.append({
                    'train_id': train_id,
                    'decision': decision,
                    'bay_id': bay_id,
                    'turnout_rank': turnout_rank,
                    'km_target': feature.expected_km_if_active if decision == "active" else 0,
                    'explain': self._generate_explanation(feature, decision)
                })

            return {
                'decisions': decisions,
                'objective_value': objective_value,
                'alerts': self._generate_alerts(decisions, features)
            }
        else:
            # Fallback to simple heuristic if optimization fails
            return await self._stage1_fallback_assignment(features, plan_date)

    def _calculate_risk_score(self, features: TrainFeatures) -> float:
        """Calculate risk score for a train (lower is better)"""
        risk_score = 0.0

        # Fitness risk (higher expiry buffer = lower risk)
        if features.fit_expiry_buffer_hours < float('inf'):
            fitness_risk = max(0, 1 - (features.fit_expiry_buffer_hours / 24))  # Risk if expires within 24h
            risk_score += fitness_risk * 0.7

        # WO risk (more critical WOs = higher risk)
        wo_risk = min(1.0, features.critical_wo_count * 0.3)
        risk_score += wo_risk * 0.3

        return risk_score

    def _generate_explanation(self, features: TrainFeatures, decision: str) -> Dict[str, Any]:
        """Generate explanation for assignment decision"""
        reasons = []
        scores = {
            'risk': self._calculate_risk_score(features),
            'brand': features.brand_rolling_deficit_h,
            'mileage': abs(features.mileage_dev)
        }

        if decision == "active":
            if features.fit_ok:
                reasons.append("All fitness certificates valid")
            if features.brand_rolling_deficit_h > 0:
                reasons.append(f"Branding deficit: {features.brand_rolling_deficit_h:.1f}h")
            if features.mileage_dev < 0:
                reasons.append("Below average mileage")
        elif decision == "standby":
            reasons.append("Maintaining standby reserve")
        elif decision == "ibl":
            if features.wo_blocking:
                reasons.append("Blocked by critical work orders")
            if features.needs_clean:
                reasons.append(f"Requires {features.clean_type} cleaning")
            if not features.fit_ok:
                reasons.append("Fitness certificates expired or invalid")

        return {
            'reasons': reasons,
            'scores': scores
        }

    def _generate_alerts(self, decisions: List[Dict], features: Dict[str, TrainFeatures]) -> List[str]:
        """Generate alerts for potential issues"""
        alerts = []

        active_count = sum(1 for d in decisions if d['decision'] == 'active')
        if active_count < settings.ACTIVE_MIN:
            alerts.append(f"Only {active_count} active trains assigned (minimum: {settings.ACTIVE_MIN})")
        if active_count > settings.ACTIVE_MAX:
            alerts.append(f"{active_count} active trains assigned (maximum: {settings.ACTIVE_MAX})")

        standby_count = sum(1 for d in decisions if d['decision'] == 'standby')
        if standby_count < settings.STANDBY_MIN:
            alerts.append(f"Only {standby_count} standby trains (minimum: {settings.STANDBY_MIN})")

        # Check for high-risk active trains
        for decision in decisions:
            if decision['decision'] == 'active':
                train_id = decision['train_id']
                feature = features[train_id]
                if feature.critical_wo_count > 0:
                    alerts.append(f"Active train {train_id} has {feature.critical_wo_count} critical WOs")
                if not feature.fit_ok:
                    alerts.append(f"Active train {train_id} has fitness issues")

        return alerts

    async def _stage1_fallback_assignment(self, features: Dict[str, TrainFeatures], plan_date: date) -> Dict[str, Any]:
        """Fallback assignment when optimization fails"""
        print("Using fallback assignment method")

        # Simple rule-based assignment
        decisions = []
        active_count = 0

        for train_id, feature in features.items():
            # Prioritize active assignment
            if (feature.fit_ok and
                not feature.wo_blocking and
                active_count < settings.ACTIVE_MAX):

                decision = "active"
                active_count += 1
            elif feature.wo_blocking or feature.needs_clean:
                decision = "ibl"
            else:
                decision = "standby"

            decisions.append({
                'train_id': train_id,
                'decision': decision,
                'bay_id': feature.current_bay if decision == "standby" else None,
                'turnout_rank': None,
                'km_target': feature.expected_km_if_active if decision == "active" else 0,
                'explain': self._generate_explanation(feature, decision)
            })

        return {
            'decisions': decisions,
            'objective_value': 0,  # Unknown for fallback
            'alerts': ["Optimization failed, used fallback assignment"]
        }

    async def _stage2_ibl_scheduling(self, plan_date: date, assignment_result: Dict) -> List[Dict[str, Any]]:
        """
        Stage 2: Schedule IBL jobs for trains assigned to IBL
        Uses resource-constrained project scheduling
        """
        ibl_trains = [d for d in assignment_result['decisions'] if d['decision'] == 'ibl']

        if not ibl_trains:
            return []

        # Get available bays
        from ..models import StablingBay
        result = await self.db.execute(
            select(StablingBay)
            .where(StablingBay.is_active == True)
        )
        bays = result.scalars().all()

        # Simple scheduling: assign each IBL train to first available bay
        ibl_gantt = []
        current_time = datetime.combine(plan_date, self.night_start, tzinfo=timezone.utc)

        for i, train_decision in enumerate(ibl_trains):
            train_id = train_decision['train_id']

            # Find available bay
            bay = bays[i % len(bays)]

            # Simple duration based on train features
            features = await self.feature_service._extract_single_train_features(train_id, plan_date)
            duration_hours = 2.0 if features.needs_clean else 1.0  # 2 hours for cleaning, 1 for other

            end_time = current_time + timedelta(hours=duration_hours)

            ibl_gantt.append({
                'train_id': train_id,
                'bay_id': bay.bay_id,
                'from_ts': current_time.isoformat(),
                'to_ts': end_time.isoformat(),
                'job_type': features.clean_type if features.needs_clean else 'maintenance',
                'assigned_crew': 'Auto-assigned',  # Would be from crew scheduling system
                'priority': 'medium'
            })

            current_time = end_time + timedelta(minutes=15)  # 15 min buffer

        return ibl_gantt

    async def _stage3_stabling_turnout(self, plan_date: date, assignment_result: Dict) -> List[Dict[str, Any]]:
        """
        Stage 3: Assign stabling bays and create turnout sequence
        """
        active_trains = [d for d in assignment_result['decisions'] if d['decision'] == 'active']

        # Get available bays
        from ..models import StablingBay
        result = await self.db.execute(
            select(StablingBay)
            .where(StablingBay.is_active == True)
        )
        bays = result.scalars().all()

        # Simple assignment: round-robin through available bays
        turnout_plan = []
        for i, train_decision in enumerate(active_trains):
            bay = bays[i % len(bays)]

            turnout_plan.append({
                'train_id': train_decision['train_id'],
                'bay_id': bay.bay_id,
                'turnout_rank': i + 1,
                'eta_exit_s': bay.access_time_min * 60,  # Convert to seconds
                'route_id': f"route_{bay.bay_id}"  # Would be from depot routes
            })

        return sorted(turnout_plan, key=lambda x: x['turnout_rank'])

    def _create_summary(self, assignment_result: Dict, ibl_schedule: List, stabling_result: List) -> Dict[str, Any]:
        """Create summary of optimization results"""
        decisions = assignment_result['decisions']

        active_count = sum(1 for d in decisions if d['decision'] == 'active')
        standby_count = sum(1 for d in decisions if d['decision'] == 'standby')
        ibl_count = sum(1 for d in decisions if d['decision'] == 'ibl')

        return {
            'active': active_count,
            'standby': standby_count,
            'ibl': ibl_count,
            'total_trains': len(decisions),
            'alerts_count': len(assignment_result.get('alerts', [])),
            'ibl_jobs_count': len(ibl_schedule),
            'optimization_success': assignment_result.get('objective_value', 0) > 0
        }

    async def _save_plan_to_database(
        self,
        plan: InductionPlan,
        result: OptimizationResult,
        plan_date: date,
    ) -> None:
        """Persist optimization results on the existing plan"""

        plan.weights_json = self.weights
        plan.status = "completed"

        # Clear previous plan items
        await self.db.execute(
            delete(InductionPlanItem).where(InductionPlanItem.plan_id == plan.plan_id)
        )

        # Clear bay occupancy for the plan date window
        day_start = datetime.combine(plan_date, datetime.min.time(), tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        await self.db.execute(
            delete(BayOccupancy)
            .where(BayOccupancy.from_ts >= day_start)
            .where(BayOccupancy.from_ts < day_end)
        )

        for item in result.items:
            bay_id = None
            if item.get("bay_id"):
                try:
                    bay_id = uuid.UUID(str(item["bay_id"]))
                except ValueError:
                    bay_id = None

            plan_item = InductionPlanItem(
                plan_id=plan.plan_id,
                train_id=item["train_id"],
                decision=item["decision"],
                bay_id=bay_id,
                turnout_rank=item.get("turnout_rank"),
                km_target=item.get("km_target"),
                explain_json=item.get("explain", {}),
            )
            self.db.add(plan_item)

        for ibl_job in result.ibl_gantt:
            from_ts = datetime.fromisoformat(ibl_job["from_ts"])
            to_ts = datetime.fromisoformat(ibl_job["to_ts"])

            occupancy = BayOccupancy(
                bay_id=uuid.UUID(str(ibl_job["bay_id"])),
                train_id=ibl_job["train_id"],
                from_ts=from_ts,
                to_ts=to_ts,
            )
            self.db.add(occupancy)

        await self.db.commit()
