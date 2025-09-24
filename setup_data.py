#!/usr/bin/env python3
"""
Data Setup Script for Kochi Metro IBL Planner
Run this script to set up initial data in the database
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, date, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import settings
from app.models import (
    Base, User, Depot, StablingBay, Train, Department,
    FitnessCertificate, JobCard, BrandingCampaign
)


async def create_test_user(session: AsyncSession):
    """Create a test user"""
    test_user = User(
        user_id="testuser",
        username="testuser",
        display_name="Test User",
        role="admin"
    )
    session.add(test_user)
    print("✅ Created test user")


async def create_departments(session: AsyncSession):
    """Create basic departments"""
    departments = [
        Department(dept_code="MECH", dept_name="Mechanical", description="Mechanical systems", is_safety_critical=True),
        Department(dept_code="ELEC", dept_name="Electrical", description="Electrical systems", is_safety_critical=True),
        Department(dept_code="CIVIL", dept_name="Civil", description="Civil engineering", is_safety_critical=False),
        Department(dept_code="SIG", dept_name="Signaling", description="Signaling systems", is_safety_critical=True),
        Department(dept_code="TEL", dept_name="Telecom", description="Telecommunication", is_safety_critical=False),
    ]

    for dept in departments:
        session.add(dept)
    print(f"✅ Created {len(departments)} departments")


async def create_depot_and_bays(session: AsyncSession):
    """Create Muttom depot and stabling bays"""
    depot = Depot(
        depot_id="MUTTOM",
        name="Muttom Depot",
        code="MUT",
        is_active=True
    )
    session.add(depot)

    # Create 15 stabling bays
    for i in range(1, 16):
        bay_id = f"B-{i"02d"}"
        bay = StablingBay(
            bay_id=bay_id,
            depot_id="MUTTOM",
            position_idx=i,
            electrified=i <= 10,  # First 10 bays are electrified
            length_m=85.0,
            access_time_min=3.0 if i <= 5 else 5.0,  # Closer bays have faster access
            is_active=True
        )
        session.add(bay)

    print("✅ Created Muttom depot with 15 stabling bays")


async def create_sample_trains(session: AsyncSession):
    """Create 25 sample trains"""
    for i in range(1, 26):
        train_id = f"TS-{i"02d"}"
        train = Train(
            train_id=train_id,
            car_count=4,
            status="standby",
            depot_id="MUTTOM"
        )
        session.add(train)
    print("✅ Created 25 sample trains")


async def create_sample_certificates(session: AsyncSession):
    """Create sample fitness certificates"""
    # Get all trains
    from sqlalchemy import select
    result = await session.execute(select(Train))
    trains = result.scalars().all()

    departments = ["MECH", "ELEC", "SIG"]

    for train in trains:
        for dept_code in departments:
            # Create valid certificates for next 6 months
            valid_from = datetime.now()
            valid_to = valid_from + timedelta(days=180)

            cert = FitnessCertificate(
                train_id=train.train_id,
                dept=dept_code,
                valid_from=valid_from,
                valid_to=valid_to,
                status="valid"
            )
            session.add(cert)

    print(f"✅ Created fitness certificates for {len(trains)} trains")


async def create_sample_job_cards(session: AsyncSession):
    """Create sample job cards"""
    from sqlalchemy import select
    result = await session.execute(select(Train).limit(10))
    trains = result.scalars().all()

    sample_jobs = [
        {
            "job_id": "JOB001",
            "train_id": trains[0].train_id,
            "status": "open",
            "priority": 2,
            "ibl_required": False,
            "title": "Brake inspection",
            "details": "Annual brake system inspection"
        },
        {
            "job_id": "JOB002",
            "train_id": trains[1].train_id,
            "status": "open",
            "priority": 3,
            "ibl_required": True,
            "title": "Deep cleaning",
            "details": "Interior deep cleaning required"
        },
        {
            "job_id": "JOB003",
            "train_id": trains[2].train_id,
            "status": "completed",
            "priority": 1,
            "ibl_required": False,
            "title": "Oil change",
            "details": "Regular maintenance oil change"
        }
    ]

    for job_data in sample_jobs:
        job = JobCard(**job_data)
        session.add(job)

    print(f"✅ Created {len(sample_jobs)} sample job cards")


async def create_sample_branding(session: AsyncSession):
    """Create sample branding campaigns"""
    campaigns = [
        BrandingCampaign(
            wrap_id="WRAP001",
            advertiser="TechCorp India",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90),
            weekly_target_hours=168.0,  # 24 hours * 7 days
            min_daily_hours=20.0,
            penalty_weight=1.5
        ),
        BrandingCampaign(
            wrap_id="WRAP002",
            advertiser="Green Energy Ltd",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=60),
            weekly_target_hours=140.0,  # 20 hours * 7 days
            min_daily_hours=15.0,
            penalty_weight=1.2
        )
    ]

    for campaign in campaigns:
        session.add(campaign)

    print(f"✅ Created {len(campaigns)} sample branding campaigns")


async def main():
    """Main setup function"""
    print("🚂 Setting up Kochi Metro IBL Planner database...")

    # Create engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            await create_test_user(session)
            await create_departments(session)
            await create_depot_and_bays(session)
            await create_sample_trains(session)
            await create_sample_certificates(session)
            await create_sample_job_cards(session)
            await create_sample_branding(session)

            await session.commit()
            print("✅ Database setup completed successfully!")

        except Exception as e:
            await session.rollback()
            print(f"❌ Database setup failed: {e}")
            raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
