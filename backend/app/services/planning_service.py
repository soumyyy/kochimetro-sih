"""
Planning Service
Main orchestrator for the induction planning system
"""
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from .feature_extraction import FeatureExtractionService
from .optimization import OptimizationService
from .fleet_service import FleetService
from ..models import (
    InductionPlan,
    InductionPlanItem,
    BayOccupancy,
    Alert,
    StablingBay,
    Train,
    Override,
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

    async def apply_override(self, plan_id: str, train_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a manual override to an existing plan item."""
        plan_uuid = self._parse_plan_id(plan_id)
        plan = await self.db.get(InductionPlan, plan_uuid)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        if plan.status == "finalized":
            raise ValueError("Cannot override a finalised plan")

        result = await self.db.execute(
            select(InductionPlanItem)
            .where(InductionPlanItem.plan_id == plan_uuid)
            .where(InductionPlanItem.train_id == train_id)
            .limit(1)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise ValueError(f"Train {train_id} not found in plan {plan_id}")

        updated_fields: Dict[str, Any] = {}

        decision = payload.get("decision")
        if decision:
            decision = str(decision).lower()
            if decision not in {"active", "standby", "ibl"}:
                raise ValueError(f"Unsupported decision '{decision}'")
            if item.decision != decision:
                item.decision = decision
                updated_fields["decision"] = decision

        if "bay_id" in payload:
            bay_value = payload.get("bay_id")
            bay_uuid = None
            if bay_value:
                try:
                    bay_uuid = uuid.UUID(str(bay_value))
                except ValueError as exc:
                    raise ValueError("Invalid bay_id supplied") from exc
            if item.bay_id != bay_uuid:
                item.bay_id = bay_uuid
                updated_fields["bay_id"] = str(bay_uuid) if bay_uuid else None

        if "turnout_rank" in payload and payload["turnout_rank"] is not None:
            turnout_rank = int(payload["turnout_rank"])
            if item.turnout_rank != turnout_rank:
                item.turnout_rank = turnout_rank
                updated_fields["turnout_rank"] = turnout_rank

        if "notes" in payload:
            notes = payload.get("notes")
            if item.notes != notes:
                item.notes = notes
                updated_fields["notes"] = notes

        reason = payload.get("reason")
        if not reason:
            raise ValueError("Override reason is required")

        explain = item.explain_json or {}
        explain.setdefault("override", {})
        explain["override"].update(
            {
                "reason": reason,
                "applied_at": datetime.utcnow().isoformat(),
            }
        )
        item.explain_json = explain

        override_record = Override(
            plan_id=plan.plan_id,
            train_id=train_id,
            reason=reason,
        )
        self.db.add(override_record)

        if plan.status == "completed":
            plan.status = "amended"

        await self.db.commit()

        return {
            "train_id": train_id,
            "decision": item.decision,
            "bay_id": str(item.bay_id) if item.bay_id else None,
            "turnout_rank": item.turnout_rank,
            "notes": item.notes,
            "explanation": item.explain_json,
            "updated_fields": updated_fields,
        }

    async def get_item_explanation(self, plan_id: str, train_id: str) -> Optional[Dict[str, Any]]:
        """Return enriched explanation data for a specific plan item."""
        plan_uuid = self._parse_plan_id(plan_id)
        plan = await self.db.get(InductionPlan, plan_uuid)
        if not plan:
            return None

        result = await self.db.execute(
            select(InductionPlanItem, Train)
            .join(Train, Train.train_id == InductionPlanItem.train_id)
            .where(InductionPlanItem.plan_id == plan_uuid)
            .where(InductionPlanItem.train_id == train_id)
            .limit(1)
        )
        row = result.first()
        if not row:
            return None
        item, train = row

        features = await self.feature_service.extract_features(plan.plan_date, [train_id])
        feature = features.get(train_id)

        feature_payload = None
        if feature:
            feature_payload = {
                "fitness_ok": feature.fit_ok,
                "fit_expiry_buffer_hours": feature.fit_expiry_buffer_hours,
                "wo_blocking": feature.wo_blocking,
                "critical_wo_count": feature.critical_wo_count,
                "total_wo_count": feature.total_wo_count,
                "brand_target_h": feature.brand_target_h,
                "brand_rolling_deficit_h": feature.brand_rolling_deficit_h,
                "expected_km_if_active": feature.expected_km_if_active,
                "mileage_dev": feature.mileage_dev,
                "needs_clean": feature.needs_clean,
                "clean_type": feature.clean_type,
                "clean_duration_min": feature.clean_duration_min,
            }

        return {
            "plan_id": plan_id,
            "plan_date": plan.plan_date.isoformat(),
            "train_id": train_id,
            "train": {
                "wrap_id": train.wrap_id,
                "brand_code": train.brand_code,
                "status": train.status,
            },
            "decision": item.decision,
            "turnout_rank": item.turnout_rank,
            "bay_id": str(item.bay_id) if item.bay_id else None,
            "notes": item.notes,
            "explanation": item.explain_json or {},
            "features": feature_payload,
        }

    async def run_what_if(self, plan_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Run a lightweight what-if scenario without persisting changes."""
        plan_uuid = self._parse_plan_id(plan_id)
        plan = await self.db.get(InductionPlan, plan_uuid)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        details = await self.get_plan_details(plan_date=plan.plan_date, include_features=True)
        if not details:
            raise ValueError("Plan details unavailable")

        base_items = details.get("items", [])
        base_summary = self._summarize_items(base_items)

        force_directives = self._parse_force(request.get("force"))
        banned_trains = self._parse_ban(request.get("ban"))
        weight_deltas = request.get("weight_deltas") or {}

        scenario_items: List[Dict[str, Any]] = []
        base_lookup = {item["train_id"]: item for item in base_items}

        for item in base_items:
            scenario_item = dict(item)

            directive = force_directives.get(item["train_id"]) if force_directives else None
            if directive:
                decision = directive.get("decision")
                if decision:
                    scenario_item["decision"] = decision
                if "bay_id" in directive:
                    scenario_item["bay_id"] = directive["bay_id"]
                if directive.get("turnout_rank") is not None:
                    scenario_item["turnout_rank"] = directive["turnout_rank"]
                if directive.get("notes") is not None:
                    scenario_item["notes"] = directive["notes"]
                scenario_item.setdefault("annotations", []).append("forced")

            if item["train_id"] in banned_trains:
                if scenario_item.get("decision") != "standby":
                    scenario_item["decision"] = "standby"
                scenario_item.setdefault("annotations", []).append("banned")

            bay_id = scenario_item.get("bay_id")
            scenario_item["bay_id"] = str(bay_id) if bay_id else None
            scenario_items.append(scenario_item)

        scenario_summary = self._summarize_items(scenario_items)
        diff = {key: scenario_summary[key] - base_summary[key] for key in ("active", "standby", "ibl")}

        adjusted_weights = dict(plan.weights_json or {})
        for key, delta in weight_deltas.items():
            try:
                delta_value = float(delta)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid weight delta for '{key}'") from exc
            adjusted_weights[key] = round(adjusted_weights.get(key, 0.0) + delta_value, 6)

        changes: List[Dict[str, Any]] = []
        for scenario_item in scenario_items:
            baseline = base_lookup.get(scenario_item["train_id"])
            if not baseline:
                continue
            delta_payload = {}
            for field in ("decision", "bay_id", "turnout_rank"):
                if str(baseline.get(field)) != str(scenario_item.get(field)):
                    delta_payload[field] = {
                        "from": baseline.get(field),
                        "to": scenario_item.get(field),
                    }
            if delta_payload:
                changes.append({
                    "train_id": scenario_item["train_id"],
                    "changes": delta_payload,
                })

        return {
            "plan_id": plan_id,
            "plan_date": plan.plan_date.isoformat(),
            "weights": {
                "original": plan.weights_json,
                "adjusted": adjusted_weights,
                "deltas": weight_deltas,
            },
            "summary": {
                "base": base_summary,
                "scenario": scenario_summary,
                "diff": diff,
            },
            "forced_trains": sorted(force_directives.keys()) if force_directives else [],
            "banned_trains": sorted(banned_trains),
            "changes": changes,
            "items": scenario_items,
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

    async def get_recent_plans(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return recent plans ordered by date desc"""
        result = await self.db.execute(
            select(InductionPlan)
            .order_by(InductionPlan.plan_date.desc())
            .limit(limit)
        )
        plans = result.scalars().all()
        plan_ids = [plan.plan_id for plan in plans]

        count_map: Dict[uuid.UUID, Dict[str, int]] = defaultdict(lambda: {"active": 0, "standby": 0, "ibl": 0})
        if plan_ids:
            counts_result = await self.db.execute(
                select(InductionPlanItem.plan_id, InductionPlanItem.decision, func.count())
                .where(InductionPlanItem.plan_id.in_(plan_ids))
                .group_by(InductionPlanItem.plan_id, InductionPlanItem.decision)
            )
            for pid, decision, count in counts_result:
                count_map[pid][decision] = count

        return [
            {
                "plan_id": str(plan.plan_id),
                "plan_date": plan.plan_date.isoformat(),
                "status": plan.status,
                "active_count": count_map[plan.plan_id]["active"],
                "standby_count": count_map[plan.plan_id]["standby"],
                "ibl_count": count_map[plan.plan_id]["ibl"],
            }
            for plan in plans
        ]

    async def list_alerts(
        self,
        resolved: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return alerts filtered by resolution state."""
        stmt = (
            select(Alert, InductionPlan.plan_date)
            .outerjoin(InductionPlan, Alert.plan_id == InductionPlan.plan_id)
            .order_by(Alert.created_at.desc())
        )
        if resolved is not None:
            stmt = stmt.where(Alert.resolved == resolved)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                "alert_id": alert.alert_id,
                "plan_id": str(alert.plan_id) if alert.plan_id else None,
                "plan_date": plan_date.isoformat() if plan_date else None,
                "severity": alert.severity,
                "message": alert.message,
                "data": alert.data,
                "resolved": alert.resolved,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
            }
            for alert, plan_date in rows
        ]

    async def resolve_alert(self, alert_id: int) -> Dict[str, Any]:
        """Mark a specific alert as resolved."""
        alert = await self.db.get(Alert, alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.resolved = True
        await self.db.commit()

        plan_date = None
        if alert.plan_id:
            plan = await self.db.get(InductionPlan, alert.plan_id)
            plan_date = plan.plan_date.isoformat() if plan else None

        return {
            "alert_id": alert.alert_id,
            "plan_id": str(alert.plan_id) if alert.plan_id else None,
            "plan_date": plan_date,
            "severity": alert.severity,
            "message": alert.message,
            "data": alert.data,
            "resolved": alert.resolved,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        }

    async def get_recent_alerts(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch recent alerts across plans"""
        result = await self.db.execute(
            select(Alert, InductionPlan.plan_date)
            .outerjoin(InductionPlan, Alert.plan_id == InductionPlan.plan_id)
            .order_by(Alert.created_at.desc())
            .limit(limit)
        )
        rows = result.all()
        return [
            {
                "alert_id": alert.alert_id,
                "plan_id": str(alert.plan_id) if alert.plan_id else None,
                "plan_date": plan_date.isoformat() if plan_date else None,
                "severity": alert.severity,
                "message": alert.message,
                "resolved": alert.resolved,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
            }
            for alert, plan_date in rows
        ]

    async def get_plan_date_range(self) -> Optional[Dict[str, str]]:
        """Return the min/max plan dates in the system"""
        result = await self.db.execute(
            select(func.min(InductionPlan.plan_date), func.max(InductionPlan.plan_date))
        )
        min_date, max_date = result.one()
        if not min_date and not max_date:
            return None
        return {
            "start": min_date.isoformat() if min_date else None,
            "end": max_date.isoformat() if max_date else None,
        }

    async def get_plan_snapshot(self, plan_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """Get counts and metadata for a plan (latest by default)"""
        plan = await self._get_plan_record(plan_date)
        if not plan:
            return None

        counts_result = await self.db.execute(
            select(InductionPlanItem.decision, func.count())
            .where(InductionPlanItem.plan_id == plan.plan_id)
            .group_by(InductionPlanItem.decision)
        )
        counts_map = {row[0]: row[1] for row in counts_result.all()}

        return {
            "plan_id": str(plan.plan_id),
            "plan_date": plan.plan_date.isoformat(),
            "status": plan.status,
            "counts": {
                "active": counts_map.get("active", 0),
                "standby": counts_map.get("standby", 0),
                "ibl": counts_map.get("ibl", 0),
            },
        }

    async def get_plan_details(
        self,
        plan_date: Optional[date] = None,
        include_features: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Return plan details, optionally enriched with feature data"""
        plan = await self._get_plan_record(plan_date)
        if not plan:
            return None

        counts_result = await self.db.execute(
            select(InductionPlanItem.decision, func.count())
            .where(InductionPlanItem.plan_id == plan.plan_id)
            .group_by(InductionPlanItem.decision)
        )
        counts_map = {row[0]: row[1] for row in counts_result.all()}

        summary = {
            "active": counts_map.get("active", 0),
            "standby": counts_map.get("standby", 0),
            "ibl": counts_map.get("ibl", 0),
            "total": sum(counts_map.values()),
        }

        if not include_features:
            return {
                "plan_id": str(plan.plan_id),
                "plan_date": plan.plan_date.isoformat(),
                "status": plan.status,
                "summary": summary,
                "items": [],
            }

        rows = await self.db.execute(
            select(InductionPlanItem, Train)
            .join(Train, Train.train_id == InductionPlanItem.train_id)
            .where(InductionPlanItem.plan_id == plan.plan_id)
            .order_by(InductionPlanItem.turnout_rank.nulls_last(), InductionPlanItem.train_id)
        )
        plan_rows = rows.all()

        bay_ids = {item.bay_id for item, _ in plan_rows if item.bay_id}
        bay_lookup: Dict[uuid.UUID, StablingBay] = {}
        if bay_ids:
            bay_result = await self.db.execute(
                select(StablingBay).where(StablingBay.bay_id.in_(bay_ids))
            )
            bay_lookup = {bay.bay_id: bay for bay in bay_result.scalars()}

        features = await self.feature_service.extract_features(plan.plan_date)

        items: List[Dict[str, Any]] = []

        for item, train in plan_rows:
            feature = features.get(item.train_id)

            priority = "low"
            if feature:
                if feature.critical_wo_count > 0 or feature.wo_blocking:
                    priority = "high"
                elif feature.brand_rolling_deficit_h > 0 or feature.needs_clean:
                    priority = "medium"

            bay = bay_lookup.get(item.bay_id) if item.bay_id else None

            items.append(
                {
                    "train_id": item.train_id,
                    "decision": item.decision,
                    "priority": priority,
                    "turnout_rank": item.turnout_rank,
                    "bay_id": str(item.bay_id) if item.bay_id else None,
                    "bay_position": bay.position_idx if bay else None,
                    "wrap_id": train.wrap_id,
                    "brand_code": train.brand_code,
                    "fitness_ok": feature.fit_ok if feature else None,
                    "wo_blocking": feature.wo_blocking if feature else None,
                    "brand_deficit": round(feature.brand_rolling_deficit_h, 2) if feature else 0.0,
                    "mileage_deviation": round(feature.mileage_dev, 1) if feature else 0.0,
                    "cleaning_needed": feature.needs_clean if feature else False,
                    "clean_type": feature.clean_type if feature else None,
                    "explanation": item.explain_json,
                }
            )

        return {
            "plan_id": str(plan.plan_id),
            "plan_date": plan.plan_date.isoformat(),
            "status": plan.status,
            "summary": summary,
            "items": items,
        }

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

    async def _count_items(self, plan_id: uuid.UUID, decision: str) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(InductionPlanItem)
            .where(InductionPlanItem.plan_id == plan_id)
            .where(InductionPlanItem.decision == decision)
        )
        return result.scalar() or 0

    async def _get_plan_record(self, plan_date: Optional[date]) -> Optional[InductionPlan]:
        if plan_date:
            result = await self.db.execute(
                select(InductionPlan).where(InductionPlan.plan_date == plan_date)
            )
            return result.scalar_one_or_none()
        return await self._get_latest_plan_record()

    async def _get_latest_plan_record(self) -> Optional[InductionPlan]:
        result = await self.db.execute(
            select(InductionPlan)
            .order_by(InductionPlan.plan_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    def _parse_plan_id(self, plan_id: str) -> uuid.UUID:
        """Convert incoming plan id to UUID"""
        if isinstance(plan_id, uuid.UUID):
            return plan_id
        try:
            return uuid.UUID(str(plan_id))
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid plan id {plan_id}") from exc
