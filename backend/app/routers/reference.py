"""Reference data endpoints used by the frontend shell views."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    Depot,
    StablingBay,
    BayOccupancy,
    Train,
    InductionPlan,
    InductionPlanItem,
)
from app.services import FeatureExtractionService, BrandingService

router = APIRouter()


async def _resolve_plan_date(db: AsyncSession, requested: Optional[date]) -> Optional[date]:
    """Return an explicit plan date (latest if none supplied)."""
    if requested:
        return requested

    stmt = select(InductionPlan.plan_date).order_by(InductionPlan.plan_date.desc()).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_plan_record(db: AsyncSession, plan_day: Optional[date]) -> Optional[InductionPlan]:
    if not plan_day:
        return None
    stmt = select(InductionPlan).where(InductionPlan.plan_date == plan_day)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@router.get("/depot", summary="Get depot information")
async def get_depot_info(
    plan_date: Optional[date] = Query(None, description="Plan day to anchor occupancy data"),
    include_occupancy: bool = Query(True, description="Include bay occupancy slices for the day"),
    db: AsyncSession = Depends(get_db),
):
    """Return depot metadata, bay inventory, and an optional occupancy snapshot."""
    resolved_date = await _resolve_plan_date(db, plan_date)
    plan = await _get_plan_record(db, resolved_date)

    depot_rows = await db.execute(select(Depot).order_by(Depot.name.asc()))
    depots = depot_rows.scalars().all()

    bay_rows = await db.execute(select(StablingBay))
    bays = bay_rows.scalars().all()

    train_rows = await db.execute(select(Train))
    trains = train_rows.scalars().all()

    bays_by_depot: Dict[str, List[StablingBay]] = defaultdict(list)
    for bay in bays:
        bays_by_depot[str(bay.depot_id)].append(bay)

    trains_by_bay: Dict[str, Dict[str, Any]] = {}
    for train in trains:
        if train.current_bay:
            trains_by_bay[str(train.current_bay)] = {
                "train_id": train.train_id,
                "status": train.status,
                "wrap_id": train.wrap_id,
            }

    assignments_by_bay: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if plan:
        item_rows = await db.execute(
            select(InductionPlanItem).where(InductionPlanItem.plan_id == plan.plan_id)
        )
        for item in item_rows.scalars():
            if not item.bay_id:
                continue
            assignments_by_bay[str(item.bay_id)].append(
                {
                    "train_id": item.train_id,
                    "decision": item.decision,
                    "turnout_rank": item.turnout_rank,
                }
            )
        for bay_list in assignments_by_bay.values():
            bay_list.sort(key=lambda entry: (entry["turnout_rank"] or 10_000, entry["train_id"]))

    occupancy_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if include_occupancy:
        occ_stmt = select(BayOccupancy).order_by(BayOccupancy.from_ts.asc())
        if resolved_date:
            occ_stmt = occ_stmt.where(func.date(BayOccupancy.from_ts) == resolved_date)
        occ_rows = await db.execute(occ_stmt)
        for occ in occ_rows.scalars():
            key = str(occ.bay_id)
            duration_hours = (occ.to_ts - occ.from_ts).total_seconds() / 3600.0
            occupancy_map[key].append(
                {
                    "train_id": occ.train_id,
                    "from_ts": occ.from_ts.isoformat(),
                    "to_ts": occ.to_ts.isoformat(),
                    "duration_hours": round(duration_hours, 2),
                }
            )

    depots_payload = []
    for depot in depots:
        depot_id = str(depot.depot_id)
        depot_bays = bays_by_depot.get(depot_id, [])
        active_bays = [bay for bay in depot_bays if bay.is_active]
        occupied_bays = [bay_id for bay_id in trains_by_bay if bay_id in {str(b.bay_id) for b in depot_bays}]

        depots_payload.append(
            {
                "depot_id": depot_id,
                "code": depot.code,
                "name": depot.name,
                "is_active": depot.is_active,
                "bay_count": len(depot_bays),
                "active_bay_count": len(active_bays),
                "occupied_bay_count": len(occupied_bays),
            }
        )

    bays_payload: List[Dict[str, Any]] = []
    for bay in bays:
        bay_id = str(bay.bay_id)
        current = trains_by_bay.get(bay_id)
        plan_assignments = assignments_by_bay.get(bay_id, [])
        occupancy_entries = occupancy_map.get(bay_id, [])
        next_turnout = plan_assignments[0]["turnout_rank"] if plan_assignments else None

        bays_payload.append(
            {
                "bay_id": bay_id,
                "depot_id": str(bay.depot_id),
                "position_idx": bay.position_idx,
                "electrified": bay.electrified,
                "length_m": float(bay.length_m or 0.0),
                "access_time_min": float(bay.access_time_min or 0.0),
                "is_active": bay.is_active,
                "current_train": current["train_id"] if current else None,
                "current_train_status": current["status"] if current else None,
                "current_wrap_id": current["wrap_id"] if current else None,
                "next_turnout_rank": next_turnout,
                "plan_assignments": plan_assignments,
                "occupancy": occupancy_entries,
            }
        )

    occupancy_payload: List[Dict[str, Any]] = []
    for bay_id, entries in occupancy_map.items():
        for entry in entries:
            occupancy_payload.append({"bay_id": bay_id, **entry})

    routes_payload: List[Dict[str, Any]] = []
    for depot in depots:
        depot_id = str(depot.depot_id)
        depot_bays = bays_by_depot.get(depot_id, [])
        if not depot_bays:
            continue
        access_times = [float(b.access_time_min or 0.0) for b in depot_bays]
        avg_access = sum(access_times) / len(access_times) if access_times else 0.0
        routes_payload.append(
            {
                "depot_id": depot_id,
                "label": f"{depot.code or depot.name} throat",
                "bay_count": len(depot_bays),
                "electrified_bays": sum(1 for b in depot_bays if b.electrified),
                "average_access_time_min": round(avg_access, 2),
                "max_access_time_min": round(max(access_times) if access_times else 0.0, 2),
            }
        )

    conflicts_payload: List[Dict[str, Any]] = []

    # Turnout rank collisions
    rank_map: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for bay_id, assignments in assignments_by_bay.items():
        for assignment in assignments:
            rank = assignment.get("turnout_rank")
            if rank is not None:
                rank_map[rank].append({"train_id": assignment["train_id"], "bay_id": bay_id})
    for rank, entries in rank_map.items():
        if len(entries) > 1:
            conflicts_payload.append(
                {
                    "type": "turnout_rank_overlap",
                    "turnout_rank": rank,
                    "entries": entries,
                    "message": f"{len(entries)} trains share turnout rank {rank}",
                }
            )

    # Occupancy overlaps
    for bay_id, entries in occupancy_map.items():
        ordered = sorted(entries, key=lambda entry: entry["from_ts"])
        for prev, curr in zip(ordered, ordered[1:]):
            prev_end = datetime.fromisoformat(prev["to_ts"])
            curr_start = datetime.fromisoformat(curr["from_ts"])
            if curr_start < prev_end:
                conflicts_payload.append(
                    {
                        "type": "occupancy_overlap",
                        "bay_id": bay_id,
                        "train_ids": [prev["train_id"], curr["train_id"]],
                        "from_ts": curr["from_ts"],
                        "to_ts": prev["to_ts"],
                        "message": "Overlapping bay occupancy detected",
                    }
                )

    for bay in bays_payload:
        if not bay["is_active"] and bay["current_train"]:
            conflicts_payload.append(
                {
                    "type": "inactive_bay_in_use",
                    "bay_id": bay["bay_id"],
                    "train_id": bay["current_train"],
                    "message": "Inactive bay has an assigned train",
                }
            )

    summary = {
        "plan_date": resolved_date.isoformat() if resolved_date else None,
        "total_depots": len(depots_payload),
        "total_bays": len(bays_payload),
        "occupied_bays": sum(1 for bay in bays_payload if bay["current_train"]),
        "assignments_available": bool(plan),
    }

    return {
        "summary": summary,
        "depots": depots_payload,
        "bays": bays_payload,
        "occupancy": occupancy_payload,
        "routes": routes_payload,
        "conflicts": conflicts_payload,
    }


@router.get("/trains", summary="Get train roster")
async def get_trains(
    plan_date: Optional[date] = Query(None, description="Plan day used for feature context"),
    db: AsyncSession = Depends(get_db),
):
    """Return train roster enriched with the latest feature snapshot."""
    resolved_date = await _resolve_plan_date(db, plan_date)
    plan = await _get_plan_record(db, resolved_date)

    train_rows = await db.execute(select(Train).order_by(Train.train_id.asc()))
    trains = train_rows.scalars().all()

    feature_service = FeatureExtractionService(db)
    features: Dict[str, Any] = {}
    if resolved_date:
        features = await feature_service.extract_features(resolved_date)

    assignments: Dict[str, Dict[str, Any]] = {}
    if plan:
        item_rows = await db.execute(
            select(InductionPlanItem).where(InductionPlanItem.plan_id == plan.plan_id)
        )
        for item in item_rows.scalars():
            assignments[item.train_id] = {
                "decision": item.decision,
                "turnout_rank": item.turnout_rank,
                "bay_id": str(item.bay_id) if item.bay_id else None,
            }

    roster_payload: List[Dict[str, Any]] = []
    status_counter: Counter[str] = Counter()

    for train in trains:
        status_counter[train.status or "unknown"] += 1
        feature = features.get(train.train_id)
        feature_payload = None
        if feature:
            feature_payload = {
                "fitness_ok": feature.fit_ok,
                "fit_expiry_buffer_hours": feature.fit_expiry_buffer_hours,
                "wo_blocking": feature.wo_blocking,
                "critical_wo_count": feature.critical_wo_count,
                "total_wo_count": feature.total_wo_count,
                "brand_target_h": round(feature.brand_target_h, 2),
                "brand_rolling_deficit_h": round(feature.brand_rolling_deficit_h, 2),
                "km_cum": round(feature.km_cum, 1),
                "mileage_dev": round(feature.mileage_dev, 1),
                "needs_clean": feature.needs_clean,
                "clean_type": feature.clean_type,
                "explanation": feature.explanation,
            }

        train_payload = {
            "train_id": train.train_id,
            "status": train.status,
            "current_bay": str(train.current_bay) if train.current_bay else None,
            "wrap_id": train.wrap_id,
            "brand_code": train.brand_code,
            "notes": train.notes,
            "plan_assignment": assignments.get(train.train_id),
            "features": feature_payload,
        }
        roster_payload.append(train_payload)

    summary = {
        "plan_date": resolved_date.isoformat() if resolved_date else None,
        "total_trains": len(roster_payload),
        "status_breakdown": dict(status_counter),
    }

    return {
        "summary": summary,
        "trains": roster_payload,
    }


@router.get("/sponsors", summary="Get sponsor information")
async def get_sponsors(
    rollup_date: Optional[date] = Query(None, description="Anchor date for exposure window"),
    window: int = Query(14, ge=1, le=90, description="Number of trailing days to aggregate"),
    db: AsyncSession = Depends(get_db),
):
    """Return sponsor and campaign performance rollups."""
    service = BrandingService(db)
    try:
        return await service.get_rollup(window=window, end_date=rollup_date)
    except ValueError as exc:  # window validation
        raise HTTPException(status_code=400, detail=str(exc)) from exc
