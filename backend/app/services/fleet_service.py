"""
Fleet Service
Provides utilities for managing fleet data and calculations
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from collections import defaultdict

from ..models import (
    Train, MileageLog, ServiceLog, BrandingExposureLog,
    FitnessCertificate, JobCard, StablingBay, Depot
)
from .feature_extraction import FeatureExtractionService


class FleetService:
    """Service for fleet-wide calculations and utilities"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.feature_service = FeatureExtractionService(db)

    async def get_fleet_overview(self) -> Dict[str, Any]:
        """Get fleet-wide overview statistics"""
        # Get all trains
        result = await self.db.execute(select(Train))
        trains = result.scalars().all()

        # Get mileage statistics
        mileage_stats = await self.get_fleet_mileage_stats()

        # Get service statistics
        service_stats = await self.get_service_compliance_stats()

        # Get fitness compliance
        fitness_stats = await self.get_fitness_compliance_stats()

        # Get availability statistics
        availability_stats = await self.get_availability_stats()

        return {
            'total_trains': len(trains),
            'active_trains': len([t for t in trains if t.status == 'active']),
            'standby_trains': len([t for t in trains if t.status == 'standby']),
            'ibl_trains': len([t for t in trains if t.status == 'ibl']),
            'mileage': mileage_stats,
            'service': service_stats,
            'fitness': fitness_stats,
            'availability': availability_stats
        }

    async def get_fleet_mileage_stats(self) -> Dict[str, Any]:
        """Get fleet-wide mileage statistics"""
        # Total mileage by train
        result = await self.db.execute(
            select(
                Train.train_id,
                func.sum(MileageLog.km_run).label('total_km')
            )
            .outerjoin(MileageLog, Train.train_id == MileageLog.train_id)
            .group_by(Train.train_id)
        )
        mileage_data = result.all()

        if not mileage_data:
            return {'average': 0, 'std_dev': 0, 'total': 0}

        mileages = [row.total_km or 0 for row in mileage_data]
        total_km = sum(mileages)
        average_km = total_km / len(mileages)

        # Calculate standard deviation
        variance = sum((x - average_km) ** 2 for x in mileages) / len(mileages)
        std_dev = variance ** 0.5

        return {
            'average': round(average_km, 1),
            'std_dev': round(std_dev, 1),
            'total': round(total_km, 1),
            'min': round(min(mileages), 1),
            'max': round(max(mileages), 1)
        }

    async def get_service_compliance_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get service compliance statistics for the last N days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Get service logs
        result = await self.db.execute(
            select(
                ServiceLog.date,
                func.count(ServiceLog.log_id).label('total_logs'),
                func.sum(func.cast(ServiceLog.actual_service, Integer)).label('actual_services')
            )
            .where(ServiceLog.date >= start_date)
            .where(ServiceLog.date <= end_date)
            .group_by(ServiceLog.date)
        )
        service_data = result.all()

        if not service_data:
            return {'compliance_rate': 0, 'total_planned': 0, 'total_actual': 0}

        total_planned = sum(row.total_logs for row in service_data)
        total_actual = sum(row.actual_services or 0 for row in service_data)
        compliance_rate = (total_actual / total_planned * 100) if total_planned > 0 else 0

        return {
            'compliance_rate': round(compliance_rate, 1),
            'total_planned': total_planned,
            'total_actual': total_actual,
            'days_analyzed': days
        }

    async def get_fitness_compliance_stats(self) -> Dict[str, Any]:
        """Get fitness certificate compliance statistics"""
        result = await self.db.execute(
            select(
                FitnessCertificate.status,
                func.count(FitnessCertificate.cert_id).label('count')
            )
            .group_by(FitnessCertificate.status)
        )
        status_counts = dict(result.all())

        total_certs = sum(status_counts.values())
        compliant_certs = status_counts.get('valid', 0) + status_counts.get('expiring', 0)
        compliance_rate = (compliant_certs / total_certs * 100) if total_certs > 0 else 0

        # Get expiring certificates (within 7 days)
        expiring_count = await self.db.execute(
            select(func.count(FitnessCertificate.cert_id))
            .where(FitnessCertificate.valid_to <= datetime.now() + timedelta(days=7))
            .where(FitnessCertificate.valid_to >= datetime.now())
            .where(FitnessCertificate.status.in_(['valid', 'expiring']))
        )
        expiring = expiring_count.scalar() or 0

        return {
            'compliance_rate': round(compliance_rate, 1),
            'total_certificates': total_certs,
            'valid_certificates': status_counts.get('valid', 0),
            'expiring_certificates': expiring,
            'expired_certificates': status_counts.get('expired', 0),
            'suspended_certificates': status_counts.get('suspended', 0)
        }

    async def get_availability_stats(self) -> Dict[str, Any]:
        """Get train availability statistics"""
        result = await self.db.execute(select(Train))
        trains = result.scalars().all()

        status_counts = {}
        for train in trains:
            status_counts[train.status] = status_counts.get(train.status, 0) + 1

        total_trains = len(trains)
        available_trains = (
            status_counts.get('active', 0) +
            status_counts.get('standby', 0)
        )
        availability_rate = (available_trains / total_trains * 100) if total_trains > 0 else 0

        return {
            'availability_rate': round(availability_rate, 1),
            'total_trains': total_trains,
            'available_trains': available_trains,
            'unavailable_trains': total_trains - available_trains,
            'status_breakdown': status_counts
        }

    async def get_trains_by_depot(self) -> Dict[str, List[Train]]:
        """Get trains grouped by depot"""
        result = await self.db.execute(
            select(Train, Depot)
            .outerjoin(Depot, Train.current_bay == Depot.depot_id)  # This might need adjustment
        )
        # For now, assume all trains are at MUTTOM depot
        trains = result.scalars().all()

        depot_groups = defaultdict(list)
        for train in trains:
            depot_groups[train.depot_id or 'MUTTOM'].append(train)

        return dict(depot_groups)

    async def get_bay_utilization(self) -> Dict[str, Any]:
        """Get stabling bay utilization statistics"""
        result = await self.db.execute(select(StablingBay))
        bays = result.scalars().all()

        total_bays = len(bays)
        active_bays = len([b for b in bays if b.is_active])

        # Count bays with current occupancy
        occupied_bays = len([b for b in bays if b.bay_id in [t.current_bay for t in await self.db.execute(select(Train.current_bay))]])

        return {
            'total_bays': total_bays,
            'active_bays': active_bays,
            'occupied_bays': occupied_bays,
            'utilization_rate': round((occupied_bays / active_bays * 100), 1) if active_bays > 0 else 0
        }

    async def get_daily_service_summary(self, target_date: date) -> Dict[str, Any]:
        """Get service summary for a specific date"""
        result = await self.db.execute(
            select(
                func.count().label('total_planned'),
                func.sum(func.cast(ServiceLog.actual_service, Integer)).label('total_actual'),
                func.avg(func.cast(ServiceLog.delay_minutes, Float)).label('avg_delay')
            )
            .where(ServiceLog.date == target_date)
        )
        row = result.first()

        if not row:
            return {
                'date': target_date.isoformat(),
                'total_planned': 0,
                'total_actual': 0,
                'compliance_rate': 0,
                'avg_delay': 0
            }

        total_planned = row.total_planned or 0
        total_actual = row.total_actual or 0
        compliance_rate = (total_actual / total_planned * 100) if total_planned > 0 else 0
        avg_delay = row.avg_delay or 0

        return {
            'date': target_date.isoformat(),
            'total_planned': total_planned,
            'total_actual': total_actual,
            'compliance_rate': round(compliance_rate, 1),
            'avg_delay': round(avg_delay, 1)
        }

    async def get_branding_performance(self, days: int = 30) -> Dict[str, Any]:
        """Get branding performance statistics"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Get exposure data
        result = await self.db.execute(
            select(
                func.sum(BrandingExposureLog.exposure_hours).label('total_exposure')
            )
            .where(BrandingExposureLog.log_date >= start_date)
            .where(BrandingExposureLog.log_date <= end_date)
        )
        total_exposure = result.scalar() or 0

        # Get campaign count
        from ..models import BrandingCampaign
        result = await self.db.execute(
            select(func.count(BrandingCampaign.wrap_id))
            .where(BrandingCampaign.start_date <= end_date)
            .where(BrandingCampaign.end_date >= start_date)
        )
        active_campaigns = result.scalar() or 0

        # Calculate average daily exposure
        avg_daily_exposure = total_exposure / days if days > 0 else 0

        return {
            'period_days': days,
            'total_exposure_hours': round(total_exposure, 1),
            'average_daily_exposure': round(avg_daily_exposure, 1),
            'active_campaigns': active_campaigns
        }

    async def get_maintenance_backlog(self) -> Dict[str, Any]:
        """Get maintenance backlog statistics"""
        # Get open job cards
        result = await self.db.execute(
            select(
                JobCard.status,
                func.count(JobCard.job_id).label('count')
            )
            .where(JobCard.status.in_(['open', 'in_progress']))
            .group_by(JobCard.status)
        )
        status_counts = dict(result.all())

        # Get overdue jobs
        overdue_result = await self.db.execute(
            select(func.count(JobCard.job_id))
            .where(JobCard.due_date < date.today())
            .where(JobCard.status.in_(['open', 'in_progress']))
        )
        overdue_count = overdue_result.scalar() or 0

        # Get critical jobs
        critical_result = await self.db.execute(
            select(func.count(JobCard.job_id))
            .where(JobCard.priority >= 3)
            .where(JobCard.status.in_(['open', 'in_progress']))
        )
        critical_count = critical_result.scalar() or 0

        total_open = sum(status_counts.values())

        return {
            'total_open_jobs': total_open,
            'overdue_jobs': overdue_count,
            'critical_jobs': critical_count,
            'status_breakdown': status_counts
        }

    async def get_emergency_readiness(self) -> Dict[str, Any]:
        """Get emergency readiness assessment"""
        # Count available trains (active + standby)
        available_result = await self.db.execute(
            select(func.count(Train.train_id))
            .where(Train.status.in_(['active', 'standby']))
        )
        available_trains = available_result.scalar() or 0

        # Count trains with valid fitness certificates
        fitness_result = await self.db.execute(
            select(func.count())
            .select_from(
                select(Train.train_id)
                .join(FitnessCertificate, Train.train_id == FitnessCertificate.train_id)
                .where(FitnessCertificate.status.in_(['valid', 'expiring']))
                .where(FitnessCertificate.valid_to >= datetime.now() + timedelta(hours=24))
                .group_by(Train.train_id)
                .having(func.count(FitnessCertificate.cert_id) >= 3)  # Assuming 3 depts needed
            )
        )
        ready_trains = fitness_result.scalar() or 0

        # Count trains without critical WOs
        wo_result = await self.db.execute(
            select(func.count())
            .select_from(
                select(Train.train_id)
                .left_join(JobCard, Train.train_id == JobCard.train_id)
                .where(
                    or_(
                        JobCard.job_id.is_(None),
                        ~JobCard.status.in_(['open', 'in_progress']),
                        JobCard.ibl_required == False
                    )
                )
                .group_by(Train.train_id)
            )
        )
        operational_trains = wo_result.scalar() or 0

        readiness_score = min(available_trains, ready_trains, operational_trains)

        return {
            'available_trains': available_trains,
            'fitness_ready_trains': ready_trains,
            'operationally_ready_trains': operational_trains,
            'readiness_score': readiness_score,
            'readiness_percentage': round((readiness_score / 25) * 100, 1)  # Assuming 25 train fleet
        }
