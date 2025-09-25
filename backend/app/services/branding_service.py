"""Branding analytics helpers."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import BrandingCampaign, BrandingExposureLog, Train, InductionPlan


class BrandingService:
    """Compute rollups for branding exposure and campaign compliance."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    async def get_rollup(self, window: int = 14, end_date: Optional[date] = None) -> Dict[str, Any]:
        """Return campaign and sponsor level rollups for the specified window."""
        if window <= 0:
            raise ValueError("window must be positive")

        window_end = await self._resolve_end_date(end_date)
        window_start = window_end - timedelta(days=window - 1)

        exposures_by_wrap = await self._get_exposure_by_wrap(window_start, window_end)
        trains_by_wrap = await self._get_trains_by_wrap()

        campaign_result = await self.db.execute(select(BrandingCampaign))
        campaigns = campaign_result.scalars().all()

        sponsor_buckets: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {
                "active_campaigns": 0,
                "total_promised_hours": 0.0,
                "total_delivered_hours": 0.0,
                "deficit_hours": 0.0,
                "over_delivery_hours": 0.0,
            }
        )

        campaign_summaries: List[Dict[str, Any]] = []

        for campaign in campaigns:
            if campaign.end_date < window_start or campaign.start_date > window_end:
                continue

            daily_target = float(campaign.weekly_target_hours or 0) / 7.0
            window_target = daily_target * window
            delivered_hours = exposures_by_wrap.get(campaign.wrap_id, 0.0)

            deficit_hours = max(window_target - delivered_hours, 0.0)
            over_delivery_hours = max(delivered_hours - window_target, 0.0)

            status = self._classify_status(delivered_hours, window_target)
            sponsor_bucket = sponsor_buckets[campaign.advertiser]
            sponsor_bucket["active_campaigns"] += 1
            sponsor_bucket["total_promised_hours"] += window_target
            sponsor_bucket["total_delivered_hours"] += delivered_hours
            sponsor_bucket["deficit_hours"] += deficit_hours
            sponsor_bucket["over_delivery_hours"] += over_delivery_hours

            campaign_summaries.append(
                {
                    "wrap_id": campaign.wrap_id,
                    "name": campaign.wrap_id,
                    "advertiser": campaign.advertiser,
                    "start_date": campaign.start_date.isoformat(),
                    "end_date": campaign.end_date.isoformat(),
                    "promised_hours_per_day": round(daily_target, 2),
                    "window_target_hours": round(window_target, 1),
                    "delivered_hours": round(delivered_hours, 1),
                    "current_deficit": round(deficit_hours, 1),
                    "status": status,
                    "penalty_weight": float(campaign.penalty_weight or 0.0),
                    "active_trains": trains_by_wrap.get(campaign.wrap_id, []),
                    "rolling_window_days": window,
                }
            )

        sponsors: List[Dict[str, Any]] = []
        for sponsor_name, bucket in sponsor_buckets.items():
            promised = bucket["total_promised_hours"]
            delivered = bucket["total_delivered_hours"]
            penalty_risk = self._classify_penalty(delivered, promised)

            sponsors.append(
                {
                    "name": sponsor_name,
                    "active_campaigns": int(bucket["active_campaigns"]),
                    "total_promised_hours": round(promised, 1),
                    "total_delivered_hours": round(delivered, 1),
                    "deficit_hours": round(bucket["deficit_hours"], 1),
                    "over_delivery_hours": round(bucket["over_delivery_hours"], 1),
                    "penalty_risk": penalty_risk,
                }
            )

        sponsors.sort(key=lambda entry: entry["deficit_hours"], reverse=True)
        campaign_summaries.sort(key=lambda entry: entry["current_deficit"], reverse=True)

        totals = {
            "deficit_hours": round(sum(s["deficit_hours"] for s in sponsors), 1),
            "over_delivery_hours": round(sum(s["over_delivery_hours"] for s in sponsors), 1),
            "active_campaigns": sum(s["active_campaigns"] for s in sponsors),
            "active_sponsors": len(sponsors),
        }

        return {
            "generated_at": window_end.isoformat(),
            "window": {
                "start": window_start.isoformat(),
                "end": window_end.isoformat(),
                "days": window,
            },
            "sponsors": sponsors,
            "campaigns": campaign_summaries,
            "totals": totals,
        }

    async def _resolve_end_date(self, end_date: Optional[date]) -> date:
        if end_date:
            return end_date

        result = await self.db.execute(select(func.max(InductionPlan.plan_date)))
        plan_date = result.scalar_one_or_none()
        return plan_date or date.today()

    async def _get_exposure_by_wrap(self, start_date: date, end_date: date) -> Dict[str, float]:
        """Return total exposure hours per wrap for the window."""
        exposure_query = (
            select(
                Train.wrap_id,
                func.sum(BrandingExposureLog.exposure_hours).label("hours"),
            )
            .join(Train, Train.train_id == BrandingExposureLog.train_id)
            .where(BrandingExposureLog.log_date >= start_date)
            .where(BrandingExposureLog.log_date <= end_date)
            .where(Train.wrap_id.is_not(None))
            .group_by(Train.wrap_id)
        )

        result = await self.db.execute(exposure_query)
        exposures: Dict[str, float] = {}
        for wrap_id, hours in result.all():
            if wrap_id:
                exposures[wrap_id] = float(hours or 0.0)
        return exposures

    async def _get_trains_by_wrap(self) -> Dict[str, List[str]]:
        """Return mapping of wrap_id to the trains currently carrying it."""
        result = await self.db.execute(select(Train).where(Train.wrap_id.is_not(None)))
        trains = result.scalars().all()

        mapping: Dict[str, List[str]] = defaultdict(list)
        for train in trains:
            if train.wrap_id:
                mapping[train.wrap_id].append(train.train_id)

        for train_list in mapping.values():
            train_list.sort()

        return dict(mapping)

    @staticmethod
    def _classify_status(delivered: float, target: float) -> str:
        """Get campaign status based on delivery versus target."""
        if target <= 0:
            return "on_track"
        ratio = delivered / target
        if ratio >= 1.0:
            return "on_track"
        if ratio >= 0.85:
            return "at_risk"
        return "behind_schedule"

    @staticmethod
    def _classify_penalty(delivered: float, target: float) -> str:
        """Classify sponsor penalty exposure based on delivery ratio."""
        if target <= 0:
            return "low"
        ratio = delivered / target
        if ratio >= 0.95:
            return "low"
        if ratio >= 0.8:
            return "medium"
        return "high"
