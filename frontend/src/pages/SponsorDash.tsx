import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import Layout from '../components/Layout'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CalendarRange,
  Users
} from 'lucide-react'
import { usePlanDate } from '../context/PlanDateContext'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

interface BrandingRollup {
  generated_at: string
  window: {
    start: string
    end: string
    days: number
  }
  sponsors: SponsorSummary[]
  campaigns: CampaignSummary[]
  totals: {
    deficit_hours: number
    over_delivery_hours: number
    active_campaigns: number
    active_sponsors: number
  }
}

interface SponsorSummary {
  name: string
  active_campaigns: number
  total_promised_hours: number
  total_delivered_hours: number
  deficit_hours: number
  over_delivery_hours: number
  penalty_risk: 'low' | 'medium' | 'high'
}

interface CampaignSummary {
  wrap_id: string
  name: string
  advertiser: string
  start_date: string
  end_date: string
  promised_hours_per_day: number
  window_target_hours: number
  delivered_hours: number
  current_deficit: number
  status: 'on_track' | 'at_risk' | 'behind_schedule'
  penalty_weight: number
  active_trains: string[]
  rolling_window_days: number
}

const fetchBrandingRollup = async (planDate: string | null): Promise<BrandingRollup> => {
  const params: Record<string, string | number> = {}
  if (planDate) {
    params.rollup_date = planDate
  }
  const { data } = await axios.get(`${API_BASE_URL}/api/v1/ref/sponsors`, {
    params,
  })
  return data
}

const formatDate = (value: string): string =>
  new Date(value).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

const getRiskColor = (risk: SponsorSummary['penalty_risk']) => {
  switch (risk) {
    case 'high':
      return 'border border-rose-300/45 bg-rose-500/20 text-rose-100'
    case 'medium':
      return 'border border-amber-300/45 bg-amber-400/20 text-amber-100'
    case 'low':
      return 'border border-emerald-300/40 bg-emerald-400/20 text-emerald-100'
    default:
      return 'border border-white/20 bg-white/10 text-white/80'
  }
}

const getStatusColor = (status: CampaignSummary['status']) => {
  switch (status) {
    case 'on_track':
      return 'border border-emerald-300/45 bg-emerald-400/20 text-emerald-100'
    case 'at_risk':
      return 'border border-amber-300/45 bg-amber-400/20 text-amber-100'
    case 'behind_schedule':
      return 'border border-rose-300/45 bg-rose-500/20 text-rose-100'
    default:
      return 'border border-white/20 bg-white/10 text-white/80'
  }
}

export default function SponsorDash() {
  const { planDate } = usePlanDate()
  const selectionKey = planDate ?? 'latest'
  const { data, isLoading, error } = useQuery({
    queryKey: ['branding-rollup', selectionKey],
    queryFn: () => fetchBrandingRollup(planDate),
  })

  const sponsors = data?.sponsors ?? []
  const campaigns = data?.campaigns ?? []
  const totals = data?.totals ?? {
    deficit_hours: 0,
    over_delivery_hours: 0,
    active_campaigns: 0,
    active_sponsors: 0,
  }

  const highRiskSponsors = useMemo(
    () => sponsors.filter((sponsor) => sponsor.penalty_risk === 'high'),
    [sponsors],
  )

  if (error) {
    return (
      <Layout>
        <div className="rounded-3xl border border-rose-300/40 bg-rose-500/20 p-6 text-sm text-rose-100 backdrop-blur-xl">
          Unable to load branding analytics. Confirm the backend is reachable and seeded.
        </div>
      </Layout>
    )
  }

  if (isLoading) {
    return (
      <Layout>
        <div className="space-y-10 text-white">
          <div className="h-10 w-56 rounded-full bg-white/10 animate-pulse" />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div key={idx} className="h-24 rounded-3xl bg-white/10 animate-pulse" />
            ))}
          </div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="h-[420px] rounded-3xl bg-white/10 animate-pulse" />
            <div className="h-[420px] rounded-3xl bg-white/10 animate-pulse" />
          </div>
        </div>
      </Layout>
    )
  }

  if (!data) {
    return (
      <Layout>
        <div className="rounded-3xl border border-white/15 bg-white/10 p-8 text-sm text-white/70 backdrop-blur-xl">
          No branding rollup available. Import exposure data to see campaign performance.
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-10 text-white">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-white">Sponsor dashboard</h1>
            <p className="mt-2 text-sm text-white/70">
              Exposure rollup · {formatDate(data.window.start)} – {formatDate(data.window.end)}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant={totals.deficit_hours > 0 ? 'warning' : 'success'}>
              {totals.deficit_hours > 0
                ? `${totals.deficit_hours.toFixed(1)}h deficit`
                : 'All targets met'}
            </Badge>
            <Badge variant="secondary">Active sponsors: {totals.active_sponsors}</Badge>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <SummaryCard
            label="Active sponsors"
            value={totals.active_sponsors}
            icon={Users}
            accent="text-sky-200"
          />
          <SummaryCard
            label="Active campaigns"
            value={totals.active_campaigns}
            icon={BarChart3}
            accent="text-indigo-200"
          />
          <SummaryCard
            label="Total deficit (h)"
            value={totals.deficit_hours.toFixed(1)}
            icon={TrendingDown}
            accent="text-rose-200"
          />
          <SummaryCard
            label="Over-delivery (h)"
            value={totals.over_delivery_hours.toFixed(1)}
            icon={TrendingUp}
            accent="text-emerald-200"
          />
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="border-white/12 bg-white/8">
            <CardHeader>
              <CardTitle className="text-white">Top sponsors</CardTitle>
            </CardHeader>
            <CardContent>
              {sponsors.length === 0 ? (
                <div className="rounded-xl border border-dashed border-white/25 bg-white/5 p-10 text-center text-sm text-white/60">
                  No sponsor data available for the selected window.
                </div>
              ) : (
                <div className="space-y-3">
                  {sponsors.map((sponsor) => (
                    <div
                      key={sponsor.name}
                      className="rounded-xl border border-white/15 bg-white/10 p-4 text-white/80"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm font-semibold text-white">{sponsor.name}</div>
                          <div className="text-xs text-white/60">
                            Promised {sponsor.total_promised_hours.toFixed(1)}h · Delivered {sponsor.total_delivered_hours.toFixed(1)}h
                          </div>
                        </div>
                        <Badge className={getRiskColor(sponsor.penalty_risk)}>
                          {sponsor.penalty_risk} risk
                        </Badge>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-3 text-xs text-white/70">
                        <span>{sponsor.active_campaigns} active campaigns</span>
                        <span>
                          Deficit {sponsor.deficit_hours.toFixed(1)}h · Over-delivery {sponsor.over_delivery_hours.toFixed(1)}h
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-white/12 bg-white/8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <CalendarRange className="h-5 w-5" />
                Campaign watchlist
              </CardTitle>
            </CardHeader>
            <CardContent>
              {campaigns.length === 0 ? (
                <div className="rounded-xl border border-dashed border-white/25 bg-white/5 p-10 text-center text-sm text-white/60">
                  No campaign exposure recorded for this window.
                </div>
              ) : (
                <div className="space-y-3">
                  {campaigns.map((campaign) => (
                    <div
                      key={campaign.wrap_id}
                      className="rounded-xl border border-white/15 bg-white/10 p-4 text-white/80"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm font-semibold text-white">{campaign.name}</div>
                          <div className="text-xs text-white/60">
                            {formatDate(campaign.start_date)} – {formatDate(campaign.end_date)} · {campaign.promised_hours_per_day.toFixed(1)}h/day target
                          </div>
                        </div>
                        <Badge className={getStatusColor(campaign.status)}>{campaign.status.replace('_', ' ')}</Badge>
                      </div>
                      <div className="mt-3 grid grid-cols-1 gap-2 text-xs text-white/70 md:grid-cols-2">
                        <span>Window target {campaign.window_target_hours.toFixed(1)}h</span>
                        <span>Delivered {campaign.delivered_hours.toFixed(1)}h</span>
                        <span>Deficit {campaign.current_deficit.toFixed(1)}h</span>
                        <span>Active trains: {campaign.active_trains.length ? campaign.active_trains.join(', ') : '—'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {highRiskSponsors.length > 0 && (
          <Card className="border-white/12 bg-white/8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-rose-200">
                <AlertTriangle className="h-5 w-5" />
                High-risk sponsors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc space-y-1 pl-5 text-sm text-rose-200">
                {highRiskSponsors.map((sponsor) => (
                  <li key={sponsor.name}>
                    {sponsor.name}: deficit {sponsor.deficit_hours.toFixed(1)}h across {sponsor.active_campaigns} campaign(s)
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  )
}

function SummaryCard({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string
  value: number | string
  icon: typeof BarChart3
  accent: string
}) {
  return (
    <Card className="border-white/12 bg-white/8">
      <CardContent className="flex items-center gap-3 p-4">
        <div className="rounded-xl bg-white/15 p-2">
          <Icon className={`h-5 w-5 ${accent}`} />
        </div>
        <div>
          <div className="text-xl font-semibold text-white">{value}</div>
          <div className="text-xs uppercase tracking-wide text-white/60">{label}</div>
        </div>
      </CardContent>
    </Card>
  )
}
