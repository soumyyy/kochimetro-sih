"""
Feature Extraction Service
Extracts deterministic features from database for optimization engine
"""
import math
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..models import (
    Train,
    FitnessCertificate,
    JobCard,
    BrandingCampaign,
    BrandingExposureLog,
    StablingBay,
    CleaningSlot,
)
from ..models.mileage import MileageLog
from ..config import settings


class TrainFeatures:
    """Feature data structure for a single train"""

    def __init__(self, train_id: str):
        self.train_id = train_id

        # Fitness gates
        self.fit_ok: bool = True
        self.fit_expiry_buffer_hours: float = float("inf")

        # Work order gates
        self.wo_blocking: bool = False
        self.critical_wo_count: int = 0
        self.total_wo_count: int = 0

        # Branding
        self.active_campaign: Optional[str] = None
        self.brand_target_h: float = 0.0
        self.brand_rolling_deficit_h: float = 0.0

        # Mileage
        self.km_cum: float = 0.0
        self.expected_km_if_active: float = 0.0
        self.mileage_dev: float = 0.0

        # Cleaning
        self.needs_clean: bool = False
        self.clean_type: str = "none"
        self.clean_duration_min: int = 0
        self.skill_need: str = "basic"

        # Depot hint
        self.current_bay: Optional[str] = None
        self.exit_time_cost_hint_sec: int = 0

        # Additional data
        self.explanation: Dict[str, Any] = {}


class FeatureExtractionService:
    """Service for extracting features from database for optimization"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.service_start = time(6, 0)  # 06:00
        self.service_end = time(22, 30)  # 22:30

    async def extract_features(self, plan_date: date, train_ids: Optional[List[str]] = None) -> Dict[str, TrainFeatures]:
        """Extract features for all trains or specified trains"""
        if train_ids is None:
            result = await self.db.execute(select(Train))
            trains = result.scalars().all()
            train_ids = [t.train_id for t in trains]

        features: Dict[str, TrainFeatures] = {}

        for train_id in train_ids:
            try:
                features[train_id] = await self._extract_single_train_features(train_id, plan_date)
            except Exception as exc:  # pragma: no cover - defensive fallback
                feature = TrainFeatures(train_id)
                feature.fit_ok = False
                feature.explanation["error"] = str(exc)
                features[train_id] = feature

        return features

    async def _extract_single_train_features(self, train_id: str, plan_date: date) -> TrainFeatures:
        """Extract features for a single train"""
        features = TrainFeatures(train_id)

        train_result = await self.db.execute(select(Train).where(Train.train_id == train_id))
        train = train_result.scalar_one_or_none()
        if not train:
            raise ValueError(f"Train {train_id} not found")

        features.current_bay = str(train.current_bay) if train.current_bay else None

        await self._extract_fitness_features(features, train_id, plan_date)
        await self._extract_wo_features(features, train_id)
        await self._extract_branding_features(features, train, plan_date)
        await self._extract_mileage_features(features, train_id)
        await self._extract_cleaning_features(features, train)
        await self._extract_depot_features(features)

        return features

    async def _extract_fitness_features(self, features: TrainFeatures, train_id: str, plan_date: date) -> None:
        """Extract fitness certificate features"""
        result = await self.db.execute(
            select(FitnessCertificate)
            .where(FitnessCertificate.train_id == train_id)
            .where(FitnessCertificate.status.in_(["valid", "expiring"]))
        )
        certificates = result.scalars().all()

        if not certificates:
            features.fit_ok = False
            features.explanation["fitness"] = "No valid certificates found"
            return

        service_start_dt = datetime.combine(plan_date, self.service_start)
        service_end_dt = datetime.combine(plan_date, self.service_end)

        min_expiry_buffer = float("inf")
        all_valid = True

        for cert in certificates:
            if cert.valid_from <= service_start_dt and cert.valid_to >= service_end_dt:
                buffer_hours = (cert.valid_to - service_end_dt).total_seconds() / 3600
                min_expiry_buffer = min(min_expiry_buffer, max(0, buffer_hours))
            else:
                all_valid = False
                features.explanation["fitness"] = f"{cert.dept} certificate expires before service window"
                break

        features.fit_ok = all_valid
        features.fit_expiry_buffer_hours = min_expiry_buffer if all_valid else 0.0

        if all_valid:
            features.explanation["fitness"] = (
                f"{len(certificates)} certificates valid, buffer {min_expiry_buffer:.1f}h"
            )

    async def _extract_wo_features(self, features: TrainFeatures, train_id: str) -> None:
        """Extract work order features"""
        blocking_statuses = {"WAPPR", "APPR", "INPRG", "WSCH", "WMATL"}

        result = await self.db.execute(
            select(JobCard)
            .where(JobCard.train_id == train_id)
            .where(JobCard.status.in_(blocking_statuses))
        )
        job_cards = result.scalars().all()

        features.total_wo_count = len(job_cards)

        critical_blocking = [
            job for job in job_cards
            if job.ibl_required and (job.priority or 0) >= 3
        ]

        features.critical_wo_count = len(critical_blocking)
        features.wo_blocking = bool(critical_blocking)

        if features.wo_blocking:
            features.explanation["wo"] = f"{len(critical_blocking)} critical IBL-required WOs"
        else:
            features.explanation["wo"] = f"{len(job_cards)} open WOs, none blocking"

    async def _extract_branding_features(self, features: TrainFeatures, train: Train, plan_date: date) -> None:
        """Extract branding campaign features using wrap assignment"""
        if not train.wrap_id:
            features.active_campaign = None
            features.brand_target_h = 0.0
            features.brand_rolling_deficit_h = 0.0
            features.explanation["branding"] = "No wrap assigned"
            return

        campaign_result = await self.db.execute(
            select(BrandingCampaign).where(BrandingCampaign.wrap_id == train.wrap_id)
        )
        campaign = campaign_result.scalar_one_or_none()

        if not campaign:
            features.active_campaign = train.wrap_id
            features.brand_target_h = 0.0
            features.brand_rolling_deficit_h = 0.0
            features.explanation["branding"] = "Wrap has no campaign record"
            return

        features.active_campaign = campaign.wrap_id
        features.brand_target_h = float(campaign.weekly_target_hours) / 7.0

        window_days = 7
        window_start = plan_date - timedelta(days=window_days)
        exposure_result = await self.db.execute(
            select(func.coalesce(func.sum(BrandingExposureLog.exposure_hours), 0))
            .where(BrandingExposureLog.train_id == train.train_id)
            .where(BrandingExposureLog.log_date >= window_start)
            .where(BrandingExposureLog.log_date < plan_date)
        )
        actual_hours = float(exposure_result.scalar() or 0.0)
        expected_hours = features.brand_target_h * window_days
        features.brand_rolling_deficit_h = max(0.0, expected_hours - actual_hours)

        features.explanation["branding"] = (
            f"Wrap {campaign.wrap_id}: target {features.brand_target_h:.1f}h/day, "
            f"deficit {features.brand_rolling_deficit_h:.1f}h"
        )

    async def _extract_mileage_features(self, features: TrainFeatures, train_id: str) -> None:
        """Extract mileage features"""
        total_result = await self.db.execute(
            select(func.coalesce(func.sum(MileageLog.km_run), 0)).where(MileageLog.train_id == train_id)
        )
        features.km_cum = float(total_result.scalar() or 0.0)

        features.expected_km_if_active = settings.SERVICE_HOURS * 35.0  # heuristic km

        subquery = (
            select(MileageLog.train_id, func.sum(MileageLog.km_run).label("total_km"))
            .group_by(MileageLog.train_id)
            .subquery()
        )
        fleet_result = await self.db.execute(select(func.coalesce(func.avg(subquery.c.total_km), 0)).select_from(subquery))
        fleet_avg = float(fleet_result.scalar() or 0.0)
        features.mileage_dev = features.km_cum - fleet_avg

        features.explanation["mileage"] = (
            f"Cumulative {features.km_cum:.0f}km, expected {features.expected_km_if_active:.0f}km, "
            f"deviation {features.mileage_dev:.0f}km"
        )

    async def _extract_cleaning_features(self, features: TrainFeatures, train: Train) -> None:
        """Extract cleaning requirements (placeholder)"""
        if not train.current_bay:
            features.explanation["cleaning"] = "No bay assigned; assuming clean"
            return

        upcoming_cleaning = await self.db.execute(
            select(func.count())
            .select_from(CleaningSlot)
            .where(CleaningSlot.bay_id == train.current_bay)
            .where(CleaningSlot.start_ts >= datetime.now())
        )
        scheduled = int(upcoming_cleaning.scalar() or 0)

        if scheduled:
            features.needs_clean = True
            features.clean_type = "scheduled"
            features.clean_duration_min = 90
            features.skill_need = "basic"
            features.explanation["cleaning"] = "Cleaning slot scheduled"
        else:
            features.explanation["cleaning"] = "No cleaning scheduled"

    async def _extract_depot_features(self, features: TrainFeatures) -> None:
        """Extract depot-related features"""
        if not features.current_bay:
            features.explanation["depot"] = "No bay occupancy"
            return

        bay_result = await self.db.execute(
            select(StablingBay).where(StablingBay.bay_id == features.current_bay)
        )
        bay = bay_result.scalar_one_or_none()
        if bay:
            exit_time_min = float(bay.access_time_min or 0)
            features.exit_time_cost_hint_sec = int(math.ceil(exit_time_min * 60))
            features.explanation["depot"] = (
                f"Bay {features.current_bay}, exit ~{features.exit_time_cost_hint_sec}s"
            )
        else:
            features.explanation["depot"] = "Bay record missing"

    async def get_gtfs_service_expectation(self, train_id: str, plan_date: date) -> float:
        """Placeholder for GTFS based expectation"""
        return settings.SERVICE_HOURS

    async def calculate_fleet_mileage_stats(self) -> Tuple[float, float]:
        """Calculate fleet-wide mileage statistics"""
        subquery = (
            select(MileageLog.train_id, func.sum(MileageLog.km_run).label("total_km"))
            .group_by(MileageLog.train_id)
            .subquery()
        )
        result = await self.db.execute(
            select(
                func.coalesce(func.avg(subquery.c.total_km), 0.0),
                func.coalesce(func.stddev_pop(subquery.c.total_km), 0.0),
            ).select_from(subquery)
        )
        avg_km, std_km = result.first() or (0.0, 0.0)
        return float(avg_km or 0.0), float(std_km or 0.0)
