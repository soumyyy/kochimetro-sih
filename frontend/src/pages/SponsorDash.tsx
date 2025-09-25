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

const fetchBrandingRollup = async (): Promise<BrandingRollup> => {
  const { data } = await axios.get(`${API_BASE_URL}/api/v1/ref/sponsors`)
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
      return 'bg-red-100 text-red-800'
    case 'medium':
      return 'bg-amber-100 text-amber-800'
    case 'low':
      return 'bg-emerald-100 text-emerald-800'
    default:
      return 'bg-slate-100 text-slate-700'
  }
}

const getStatusColor = (status: CampaignSummary['status']) => {
  switch (status) {
    case 'on_track':
      return 'bg-emerald-100 text-emerald-800'
    case 'at_risk':
      return 'bg-amber-100 text-amber-800'
    case 'behind_schedule':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-slate-100 text-slate-700'
  }
}

export default function SponsorDash() {
  const { data, isLoading, error } = useQuery({ queryKey: ['branding-rollup'], queryFn: fetchBrandingRollup })

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
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-800">
          Unable to load branding analytics. Confirm the backend is reachable and seeded.
        </div>
      </Layout>
    )
  }

  if (isLoading) {
    return (
      <Layout>
        <div className="space-y-6">
          <div className="h-8 w-56 rounded bg-slate-200 animate-pulse" />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div key={idx} className="h-24 rounded-2xl bg-slate-100 animate-pulse" />
            ))}
          </div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="h-[420px] rounded-2xl bg-slate-100 animate-pulse" />
            <div className="h-[420px] rounded-2xl bg-slate-100 animate-pulse" />
          </div>
        </div>
      </Layout>
    )
  }

  if (!data) {
    return (
      <Layout>
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-600">
          No branding rollup available. Import exposure data to see campaign performance.
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Sponsor Dashboard</h1>
            <p className="mt-1 text-sm text-slate-600">
              Exposure rollup · {formatDate(data.window.start)} – {formatDate(data.window.end)}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant={totals.deficit_hours > 0 ? 'warning' : 'success'}>
              {totals.deficit_hours > 0
                ? `${totals.deficit_hours.toFixed(1)}h deficit`
                : 'All targets met'}
            </Badge>
            <Badge variant="outline">Active sponsors: {totals.active_sponsors}</Badge>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <SummaryCard
            label="Active sponsors"
            value={totals.active_sponsors}
            icon={Users}
            accent="text-indigo-600"
          />
          <SummaryCard
            label="Active campaigns"
            value={totals.active_campaigns}
            icon={BarChart3}
            accent="text-blue-600"
          />
          <SummaryCard
            label="Total deficit (h)"
            value={totals.deficit_hours.toFixed(1)}
            icon={TrendingDown}
            accent="text-rose-600"
          />
          <SummaryCard
            label="Over-delivery (h)"
            value={totals.over_delivery_hours.toFixed(1)}
            icon={TrendingUp}
            accent="text-emerald-600"
          />
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Top sponsors</CardTitle>
            </CardHeader>
            <CardContent>
              {sponsors.length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-10 text-center text-sm text-slate-500">
                  No sponsor data available for the selected window.
                </div>
              ) : (
                <div className="space-y-3">
                  {sponsors.map((sponsor) => (
                    <div
                      key={sponsor.name}
                      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm font-semibold text-slate-900">{sponsor.name}</div>
                          <div className="text-xs text-slate-500">
                            Promised {sponsor.total_promised_hours.toFixed(1)}h · Delivered {sponsor.total_delivered_hours.toFixed(1)}h
                          </div>
                        </div>
                        <Badge className={getRiskColor(sponsor.penalty_risk)}>
                          {sponsor.penalty_risk} risk
                        </Badge>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-600">
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

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CalendarRange className="h-5 w-5" />
                Campaign watchlist
              </CardTitle>
            </CardHeader>
            <CardContent>
              {campaigns.length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-10 text-center text-sm text-slate-500">
                  No campaign exposure recorded for this window.
                </div>
              ) : (
                <div className="space-y-3">
                  {campaigns.map((campaign) => (
                    <div
                      key={campaign.wrap_id}
                      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm font-semibold text-slate-900">{campaign.name}</div>
                          <div className="text-xs text-slate-500">
                            {formatDate(campaign.start_date)} – {formatDate(campaign.end_date)} · {campaign.promised_hours_per_day.toFixed(1)}h/day target
                          </div>
                        </div>
                        <Badge className={getStatusColor(campaign.status)}>{campaign.status.replace('_', ' ')}</Badge>
                      </div>
                      <div className="mt-3 grid grid-cols-1 gap-2 text-xs text-slate-600 md:grid-cols-2">
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
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-rose-700">
                <AlertTriangle className="h-5 w-5" />
                High-risk sponsors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc space-y-1 pl-5 text-sm text-rose-700">
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
    <Card className="rounded-2xl border border-slate-200/60 bg-white/90 shadow-sm backdrop-blur">
      <CardContent className="flex items-center gap-3 p-4">
        <div className="rounded-xl bg-slate-100 p-2">
          <Icon className={`h-5 w-5 ${accent}`} />
        </div>
        <div>
          <div className="text-xl font-semibold text-slate-900">{value}</div>
          <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
        </div>
      </CardContent>
    </Card>
  )
}
