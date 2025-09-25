#!/usr/bin/env python3
"""Seed Supabase Postgres with synthetic Kochi Metro datasets."""
from __future__ import annotations

import asyncio
import csv
import sys
import uuid
from collections import defaultdict
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from sqlalchemy import text, select

# Ensure backend package is importable
ROOT = Path(__file__).resolve().parents[1]
SYS_PATHS = [ROOT / "backend", ROOT]
for p in SYS_PATHS:
    sys.path.insert(0, str(p))

from app.database import async_session  # type: ignore  # noqa: E402
from app.models import (  # type: ignore  # noqa: E402
    Depot,
    StablingBay,
    Train,
    BrandingCampaign,
    BrandingExposureLog,
    FitnessCertificate,
    JobCard,
    MileageLog,
    InductionPlan,
    InductionPlanItem,
    BayOccupancy,
    Alert,
)

DATA_ROOT = ROOT / "data" / "kmrl_data" / "synthetic" / "latest"
DEFAULT_DEPOT_NAME = "Muttom Depot"
DEFAULT_DEPOT_CODE = "MUT"

# Durations (hours) for IBL based on cleaning type
CLEANING_DURATION = {
    "deep": 3.0,
    "light": 1.8,
    "quick": 1.0,
    "scheduled": 2.0,
}


def load_csv(name: str) -> List[Dict[str, str]]:
    path = DATA_ROOT / name
    with path.open("r", newline="") as fh:
        reader = csv.DictReader(fh)
        return [dict(row) for row in reader]


def to_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


async def truncate_all(session) -> None:
    tables = [
        "bay_occupancy",
        "alerts",
        "overrides",
        "induction_plan_items",
        "induction_plans",
        "branding_exposure_log",
        "branding_campaigns",
        "fitness_certificates",
        "job_cards",
        "mileage_log",
        "trains",
        "stabling_bays",
        "depots",
    ]
    await session.execute(text("TRUNCATE TABLE " + ", ".join(tables) + " RESTART IDENTITY CASCADE"))
    await session.commit()


async def seed_depot_and_bays(session, geometry_rows: List[Dict[str, str]]) -> Tuple[Dict[int, uuid.UUID], Dict[str, uuid.UUID]]:
    depot = Depot(name=DEFAULT_DEPOT_NAME, code=DEFAULT_DEPOT_CODE, is_active=True)
    session.add(depot)
    await session.flush()

    # Use latest date snapshot to derive bay positions
    rows_by_pos: Dict[int, List[Dict[str, str]]] = defaultdict(list)
    latest_date = max(to_date(r["date"]) for r in geometry_rows)
    latest_rows = [r for r in geometry_rows if to_date(r["date"]) == latest_date]
    for row in latest_rows:
        rows_by_pos[int(row["stabling_position"])].append(row)

    position_to_bay: Dict[int, uuid.UUID] = {}
    train_to_bay: Dict[str, uuid.UUID] = {}

    for position in sorted(rows_by_pos):
        samples = rows_by_pos[position]
        avg_access = sum(float(r["access_time_min"]) for r in samples) / len(samples)
        bay = StablingBay(
            depot_id=depot.depot_id,
            position_idx=position,
            electrified=position <= 10,
            length_m=Decimal("85.0"),
            access_time_min=Decimal(f"{avg_access:.2f}"),
            is_active=True,
        )
        session.add(bay)
        await session.flush()
        position_to_bay[position] = bay.bay_id

    # Map trains to bays based on last snapshot
    for row in latest_rows:
        position = int(row["stabling_position"])
        train_to_bay[row["train_id"].strip()] = position_to_bay[position]

    return position_to_bay, train_to_bay


async def seed_trains(session, train_rows, status_rows, train_to_bay):
    # Map latest status per train
    status_history: Dict[str, Tuple[date, str]] = {}
    for row in status_rows:
        row_date = to_date(row["date"])
        train_id = row["train_id"].strip()
        status_history.setdefault(train_id, (date.min, "standby"))
        if row_date >= status_history[train_id][0]:
            mapped = {
                "service": "active",
                "standby": "standby",
                "maintenance": "ibl",
            }.get(row["status"].strip().lower(), "standby")
            status_history[train_id] = (row_date, mapped)

    for idx, row in enumerate(train_rows):
        train_id = row["train_id"].strip()
        status = status_history.get(train_id, (date.today(), row.get("status", "standby")))[1]
        train = Train(
            train_id=train_id,
            car_count=int(row.get("car_count", 4)),
            brand_code=row.get("brand_code") or None,
            wrap_id=row.get("wrap_id") or None,
            status=status,
            current_bay=train_to_bay.get(train_id),
            notes=row.get("notes") or None,
        )
        session.add(train)
    await session.flush()


async def seed_branding(session, train_rows, exposure_rows):
    wrap_ids = {row.get("wrap_id") for row in train_rows if row.get("wrap_id")}
    base_start = min(to_date(r["date"]) for r in exposure_rows)
    base_end = max(to_date(r["date"]) for r in exposure_rows) + timedelta(days=30)

    for wrap in wrap_ids:
        campaign = BrandingCampaign(
            wrap_id=wrap,
            advertiser=f"Sponsor {wrap[-2:]}",
            start_date=base_start,
            end_date=base_end,
            weekly_target_hours=Decimal("150.0"),
            min_daily_hours=Decimal("6.0"),
            penalty_weight=Decimal("1.5"),
        )
        session.add(campaign)

    for row in exposure_rows:
        session.add(
            BrandingExposureLog(
                train_id=row["train_id"].strip(),
                log_date=to_date(row["date"]),
                exposure_hours=Decimal(row["branding_hours_today"] or "0"),
            )
        )
    await session.flush()


async def seed_fitness(session, fitness_rows):
    # Use latest snapshot per train to derive validity
    latest_by_train: Dict[str, Dict[str, str]] = {}
    latest_date = date.min
    for row in fitness_rows:
        row_date = to_date(row["date"])
        if row_date >= latest_date:
            latest_date = row_date
        latest_by_train[row["train_id"].strip()] = row

    for train_id, row in latest_by_train.items():
        for dept_key, dept_name in [("fitness_rs", "RS"), ("fitness_sig", "SIG"), ("fitness_tel", "TEL")]:
            is_valid = row.get(dept_key, "True").strip().lower() == "true"
            valid_from = datetime.combine(latest_date - timedelta(days=60), time(0, 0))
            valid_to = datetime.combine(latest_date + (timedelta(days=45) if is_valid else timedelta(days=-1)), time(23, 55))
            cert = FitnessCertificate(
                train_id=train_id,
                dept=dept_name,
                valid_from=valid_from,
                valid_to=valid_to,
                status="valid" if is_valid else "expired",
                source_ref=f"SYN-{dept_name}-{train_id}"
            )
            session.add(cert)
    await session.flush()


async def seed_mileage(session, mileage_rows):
    for row in mileage_rows:
        session.add(
            MileageLog(
                train_id=row["train_id"].strip(),
                log_date=to_date(row["date"]),
                km_run=Decimal(row["total_mileage_km"] or "0"),
            )
        )
    await session.flush()


def generate_job_entries(row: Dict[str, str]) -> Iterable[JobCard]:
    row_date = to_date(row["date"])
    train_id = row["train_id"].strip()
    critical = int(row.get("open_critical_jobcards", 0) or 0)
    noncritical = int(row.get("open_noncritical_jobcards", 0) or 0)
    priority_hint = int(row.get("priority_hint", 3) or 3)

    for idx in range(critical):
        yield JobCard(
            job_id=f"CRIT-{train_id}-{row_date:%Y%m%d}-{idx}",
            train_id=train_id,
            source="synthetic",
            status="INPRG",
            priority=max(1, min(5, priority_hint)),
            due_date=row_date + timedelta(days=1),
            ibl_required=True,
            title="Critical maintenance",
            details="Synthetic critical maintenance job",
        )
    for idx in range(noncritical):
        yield JobCard(
            job_id=f"NONC-{train_id}-{row_date:%Y%m%d}-{idx}",
            train_id=train_id,
            source="synthetic",
            status="OPEN",
            priority=max(1, min(5, priority_hint + 1)),
            due_date=row_date + timedelta(days=3),
            ibl_required=False,
            title="Routine upkeep",
            details="Synthetic non-critical work order",
        )


async def seed_job_cards(session, job_rows):
    latest_date = max(to_date(r["date"]) for r in job_rows)
    latest_rows = [r for r in job_rows if to_date(r["date"]) == latest_date]
    for row in latest_rows:
        for job in generate_job_entries(row):
            session.add(job)
    await session.flush()


async def seed_plans(session, status_rows, cleaning_rows, train_to_bay):
    cleaning_map: Dict[Tuple[date, str], str] = {}
    for row in cleaning_rows:
        cleaning_map[(to_date(row["date"]), row["train_id"].strip())] = row.get("cleaning_type", "quick").lower()

    status_by_date: Dict[date, List[Dict[str, str]]] = defaultdict(list)
    for row in status_rows:
        status_by_date[to_date(row["date"])].append(row)

    position_turnout: Dict[date, int] = {}

    for plan_date, rows in sorted(status_by_date.items()):
        plan = InductionPlan(
            plan_date=plan_date,
            status="completed",
            weights_json={
                'w_risk': 1.0,
                'w_brand': 0.6,
                'w_mileage': 0.2,
                'w_clean': 0.4,
                'w_shunt': 0.15,
                'w_override': 3.0,
            },
            notes="Synthetic plan seeded from dataset"
        )
        session.add(plan)
        await session.flush()

        active_rank = 1
        ibl_train_entries: List[Tuple[str, str]] = []

        for row in rows:
            train_id = row["train_id"].strip()
            status = row["status"].strip().lower()
            decision = {
                'service': 'active',
                'standby': 'standby',
                'maintenance': 'ibl',
            }.get(status, 'standby')
            bay_id = train_to_bay.get(train_id)
            turnout_rank = active_rank if decision == 'active' else None
            if decision == 'active':
                active_rank += 1

            explain = {
                'source_status': status,
                'withdrawal_event': int(row.get('withdrawal_event', 0) or 0),
            }

            item = InductionPlanItem(
                plan_id=plan.plan_id,
                train_id=train_id,
                decision=decision,
                bay_id=bay_id if decision in {'ibl', 'standby'} else None,
                turnout_rank=turnout_rank,
                km_target=None,
                explain_json=explain,
            )
            session.add(item)

            if decision == 'ibl' and bay_id:
                cleaning_type = cleaning_map.get((plan_date, train_id), 'deep')
                ibl_train_entries.append((train_id, cleaning_type))

        # Generate bay occupancy schedule
        current_start = datetime.combine(plan_date, time(21, 0), tzinfo=datetime.now().astimezone().tzinfo)
        for train_id, cleaning_type in ibl_train_entries:
            duration_hours = CLEANING_DURATION.get(cleaning_type, 2.0)
            from_ts = current_start
            to_ts = from_ts + timedelta(hours=duration_hours)
            current_start = to_ts + timedelta(minutes=20)

            session.add(
                BayOccupancy(
                    bay_id=train_to_bay.get(train_id),
                    train_id=train_id,
                    from_ts=from_ts,
                    to_ts=to_ts,
                )
            )

    await session.flush()


async def seed_alerts(session, alert_rows, plan_lookup):
    for row in alert_rows:
        alert_date = to_date(row["date"])
        plan = plan_lookup.get(alert_date)
        if not plan:
            continue
        alert = Alert(
            plan_id=plan.plan_id,
            severity=row.get("severity", "info"),
            message=row.get("message", ""),
            data={},
            resolved=False,
        )
        session.add(alert)
    await session.flush()


async def main() -> None:
    train_master = load_csv("train_master.csv")
    stabling_geometry = load_csv("stabling_geometry.csv")
    status_rows = load_csv("train_status_labels.csv")
    branding_rows = load_csv("branding_priorities.csv")
    fitness_rows = load_csv("fitness_certificates.csv")
    job_rows = load_csv("jobcards.csv")
    mileage_rows = load_csv("mileage_records.csv")
    cleaning_rows = load_csv("cleaning_slots.csv")
    alert_rows = load_csv("demo_alerts.csv")

    async with async_session() as session:
        await truncate_all(session)

        position_to_bay, train_to_bay = await seed_depot_and_bays(session, stabling_geometry)
        await seed_trains(session, train_master, status_rows, train_to_bay)
        await seed_branding(session, train_master, branding_rows)
        await seed_fitness(session, fitness_rows)
        await seed_mileage(session, mileage_rows)
        await seed_job_cards(session, job_rows)
        await seed_plans(session, status_rows, cleaning_rows, train_to_bay)

        # Build plan lookup for alerts
        plans = await session.execute(select(InductionPlan))
        plan_lookup = {plan.plan_date: plan for plan in plans.scalars()}
        await seed_alerts(session, alert_rows, plan_lookup)

        await session.commit()

    print("✅ Supabase database seeded with synthetic data")


if __name__ == "__main__":
    asyncio.run(main())
