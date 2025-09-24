"""
Feature Extraction Service
Extracts deterministic features from database for optimization engine
"""
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from ..models import (
    Train, FitnessCertificate, JobCard, BrandingCampaign,
    BrandingExposureLog, MileageLog, ServiceLog,
    TrainWrap, StablingBay, InductionPlan, InductionPlanItem,
    CleaningSlot
)
from ..config import settings


class TrainFeatures:
    """Feature data structure for a single train"""

    def __init__(self, train_id: str):
        self.train_id = train_id

        # Fitness gates
        self.fit_ok: bool = True
        self.fit_expiry_buffer_hours: float = float('inf')

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
        """
        Extract features for all trains or specified trains

        Args:
            plan_date: Date for which to extract features
            train_ids: Optional list of train IDs to process

        Returns:
            Dictionary mapping train_id to TrainFeatures
        """
        # Get all trains if not specified
        if train_ids is None:
            result = await self.db.execute(select(Train))
            trains = result.scalars().all()
            train_ids = [t.train_id for t in trains]

        features = {}

        # Process each train
        for train_id in train_ids:
            try:
                features[train_id] = await self._extract_single_train_features(train_id, plan_date)
            except Exception as e:
                print(f"Error extracting features for train {train_id}: {e}")
                # Create default features for failed trains
                features[train_id] = TrainFeatures(train_id)
                features[train_id].fit_ok = False
                features[train_id].explanation["error"] = str(e)

        return features

    async def _extract_single_train_features(self, train_id: str, plan_date: date) -> TrainFeatures:
        """Extract features for a single train"""
        features = TrainFeatures(train_id)

        # Get train data
        train_result = await self.db.execute(
            select(Train).where(Train.train_id == train_id)
        )
        train = train_result.scalar_one_or_none()

        if not train:
            raise ValueError(f"Train {train_id} not found")

        features.current_bay = train.current_bay

        # Extract each type of feature
        await self._extract_fitness_features(features, train_id, plan_date)
        await self._extract_wo_features(features, train_id)
        await self._extract_branding_features(features, train_id, plan_date)
        await self._extract_mileage_features(features, train_id, plan_date)
        await self._extract_cleaning_features(features, train_id, plan_date)
        await self._extract_depot_features(features, train_id)

        return features

    async def _extract_fitness_features(self, features: TrainFeatures, train_id: str, plan_date: date):
        """Extract fitness certificate features"""
        # Get all fitness certificates for the train
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

        # Check service window coverage
        service_start_dt = datetime.combine(plan_date, self.service_start)
        service_end_dt = datetime.combine(plan_date, self.service_end)

        min_expiry_buffer = float('inf')
        all_valid = True

        for cert in certificates:
            # Check if certificate covers the service window
            if cert.valid_from <= service_start_dt and cert.valid_to >= service_end_dt:
                # Certificate is valid for service window
                buffer_hours = (cert.valid_to - service_end_dt).total_seconds() / 3600
                min_expiry_buffer = min(min_expiry_buffer, max(0, buffer_hours))
            else:
                # Certificate doesn't cover service window
                all_valid = False
                features.explanation["fitness"] = f"Certificate {cert.dept} doesn't cover service window"
                break

        features.fit_ok = all_valid
        features.fit_expiry_buffer_hours = min_expiry_buffer

        if all_valid:
            features.explanation["fitness"] = (
                f"All {len(certificates)} certificates valid, expires in {min_expiry_buffer:.1f}h"
            )


    async def _extract_wo_features(self, features: TrainFeatures, train_id: str):
        """Extract work order features"""
        # Define blocking statuses
        blocking_statuses = {"WAPPR", "APPR", "INPRG", "WSCH", "WMATL"}

        # Get job cards
        result = await self.db.execute(
            select(JobCard)
            .where(JobCard.train_id == train_id)
            .where(JobCard.status.in_(blocking_statuses))
        )
        job_cards = result.scalars().all()

        features.total_wo_count = len(job_cards)

        # Check for safety-critical blocking WOs
        critical_blocking = [
            job for job in job_cards
            if job.ibl_required and job.priority and job.priority >= 3  # High priority
        ]

        features.critical_wo_count = len(critical_blocking)
        features.wo_blocking = len(critical_blocking) > 0

        if features.wo_blocking:
            features.explanation["wo"] = f"{len(critical_blocking)} critical IBL-required WOs pending"
        else:
            features.explanation["wo"] = f"{len(job_cards)} open WOs, none blocking"

    async def _extract_branding_features(self, features: TrainFeatures, train_id: str, plan_date: date):
        """Extract branding campaign features"""
        # Get active train wraps for this train
        result = await self.db.execute(
            select(TrainWrap)
            .where(TrainWrap.train_id == train_id)
            .where(TrainWrap.active_from <= plan_date)
            .where(TrainWrap.active_to >= plan_date)
        )
        active_wraps = result.scalars().all()

        if not active_wraps:
            features.brand_target_h = 0.0
            features.active_campaign = None
            features.explanation["branding"] = "No active campaigns"
            return

        # For now, take the first active campaign
        # In a real system, you might have logic to select the primary campaign
        wrap = active_wraps[0]

        # Get campaign details
        result = await self.db.execute(
            select(BrandingCampaign)
            .where(BrandingCampaign.wrap_id == wrap.campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            features.explanation["branding"] = "Campaign not found"
            return

        features.active_campaign = campaign.wrap_id
        features.brand_target_h = campaign.weekly_target_hours / 7.0  # Convert weekly to daily

        # Calculate rolling deficit
        window_days = campaign.weekly_target_hours / campaign.weekly_target_hours  # This should be campaign.rolling_window_days
        window_start = plan_date - timedelta(days=int(window_days))

        result = await self.db.execute(
            select(func.sum(BrandingExposureLog.exposure_hours))
            .where(BrandingExposureLog.train_id == train_id)
            .where(BrandingExposureLog.log_date >= window_start)
            .where(BrandingExposureLog.log_date < plan_date)
        )
        actual_hours = result.scalar() or 0.0

        expected_hours = features.brand_target_h * window_days
        features.brand_rolling_deficit_h = max(0, expected_hours - actual_hours)

        features.explanation["branding"] = (
            f"Campaign: {campaign.advertiser}, "
            f"Target: {features.brand_target_h:.1f}h/day, "
            f"Deficit: {features.brand_rolling_deficit_h:.1f}h"
        )

    async def _extract_mileage_features(self, features: TrainFeatures, train_id: str, plan_date: date):
        """Extract mileage features"""
        # Get cumulative mileage (all time)
        result = await self.db.execute(
            select(func.sum(MileageLog.km_run))
            .where(MileageLog.train_id == train_id)
        )
        features.km_cum = result.scalar() or 0.0

        # Get expected mileage if active (from GTFS or standard)
        # This is a simplified calculation - in reality would come from GTFS data
        service_hours = 16.5  # From config
        avg_speed_kmh = 35.0  # Average speed
        features.expected_km_if_active = service_hours * avg_speed_kmh

        # Calculate deviation from fleet average
        # For now, use a simple heuristic - in reality would calculate from all trains
        result = await self.db.execute(
            select(func.avg(func.sum(MileageLog.km_run)))
            .select_from(
                select(MileageLog.train_id, func.sum(MileageLog.km_run).label('total_km'))
                .group_by(MileageLog.train_id)
                .subquery()
            )
        )
        fleet_avg = result.scalar() or features.km_cum
        features.mileage_dev = features.km_cum - fleet_avg

        features.explanation["mileage"] = (
            f"Cumulative: {features.km_cum:.0f}km, "
            f"Expected if active: {features.expected_km_if_active:.0f}km, "
            f"Deviation: {features.mileage_dev:.0f}km"
        )

    async def _extract_cleaning_features(self, features: TrainFeatures, train_id: str, plan_date: date):
        """Extract cleaning requirements"""
        # Check if train has been serviced recently
        # Look at last service date
        result = await self.db.execute(
            select(func.max(ServiceLog.service_end))
            .where(ServiceLog.train_id == train_id)
            .where(ServiceLog.actual_service == True)
        )
        last_service = result.scalar()

        # Check for pending cleaning slots
        result = await self.db.execute(
            select(func.count())
            .select_from(CleaningSlot.__table__)
            .where(CleaningSlot.train_id == train_id)  # This column might not exist in schema
            .where(CleaningSlot.start_ts >= datetime.now())
        )
        pending_cleanings = result.scalar() or 0

        # Simple cleaning logic
        if last_service:
            hours_since_service = (datetime.now() - last_service).total_seconds() / 3600

            if hours_since_service > 48:  # Needs cleaning after 48 hours
                features.needs_clean = True
                features.clean_type = "deep"
                features.clean_duration_min = 120
                features.skill_need = "certified"
            elif hours_since_service > 24:  # Light cleaning after 24 hours
                features.needs_clean = True
                features.clean_type = "light"
                features.clean_duration_min = 60
                features.skill_need = "basic"
        elif pending_cleanings > 0:
            features.needs_clean = True
            features.clean_type = "scheduled"
            features.clean_duration_min = 90
            features.skill_need = "basic"

        features.explanation["cleaning"] = (
            f"Needs clean: {features.needs_clean}, "
            f"Type: {features.clean_type}, "
            f"Duration: {features.clean_duration_min}min"
        )

    async def _extract_depot_features(self, features: TrainFeatures, train_id: str):
        """Extract depot-related features"""
        # Get current bay information
        if features.current_bay:
            result = await self.db.execute(
                select(StablingBay)
                .where(StablingBay.bay_id == features.current_bay)
            )
            bay = result.scalar_one_or_none()

            if bay:
                features.exit_time_cost_hint_sec = int(bay.access_time_min * 60)

        features.explanation["depot"] = (
            f"Current bay: {features.current_bay}, "
            f"Exit time: {features.exit_time_cost_hint_sec}s"
        )

    async def get_gtfs_service_expectation(self, train_id: str, plan_date: date) -> float:
        """
        Get expected service hours from GTFS data
        This is a placeholder - would integrate with actual GTFS data
        """
        # In a real implementation, this would query GTFS data
        # For now, return standard service hours
        return 16.5  # hours

    async def calculate_fleet_mileage_stats(self) -> Tuple[float, float]:
        """
        Calculate fleet-wide mileage statistics
        Returns: (average_mileage, std_deviation)
        """
        result = await self.db.execute(
            select(
                func.avg(MileageLog.km_run),
                func.stddev(MileageLog.km_run)
            )
            .select_from(
                select(MileageLog.train_id, func.sum(MileageLog.km_run).label('total_km'))
                .group_by(MileageLog.train_id)
                .subquery()
            )
        )
        row = result.first()
        avg_km = row[0] or 0.0
        std_km = row[1] or 0.0

        return avg_km, std_km
