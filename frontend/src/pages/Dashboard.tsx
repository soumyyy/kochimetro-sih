import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import axios from 'axios'
import Layout from '../components/Layout'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Users,
  Calendar,
  Sparkles,
  ClipboardList,
  Target,
} from 'lucide-react'
import { usePlanDate } from '../context/PlanDateContext'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

interface DashboardSummaryResponse {
  latest_plan: {
    plan_id: string
    plan_date: string
    status: string
    counts: { active: number; standby: number; ibl: number }
  } | null
  plan_details: {
    plan_id: string
    plan_date: string
    status: string
    summary: { active: number; standby: number; ibl: number; total: number }
    items: Array<PlanItem>
  } | null
  recent_plans: Array<{
    plan_id: string
    plan_date: string
    status: string
    active_count: number
    standby_count: number
    ibl_count: number
  }>
  alerts: Array<{
    alert_id: number
    plan_id: string | null
    plan_date: string | null
    severity: string
    message: string
    created_at: string | null
  }>
  fleet: {
    total_trains: number
    active_trains: number
    standby_trains: number
    ibl_trains: number
    mileage: Record<string, unknown>
    fitness: Record<string, unknown>
    availability: {
      availability_rate: number
      total_trains: number
      available_trains: number
      unavailable_trains: number
      status_breakdown: Record<string, number>
    }
  }
  branding: {
    period_days: number
    total_exposure_hours: number
    average_daily_exposure: number
    active_campaigns: number
  }
  maintenance: {
    total_open_jobs: number
    overdue_jobs: number
    critical_jobs: number
    status_breakdown: Record<string, number>
  }
  data_window: {
    start?: string | null
    end?: string | null
  } | null
}

interface PlanItem {
  train_id: string
  decision: 'active' | 'standby' | 'ibl'
  priority: 'high' | 'medium' | 'low'
  turnout_rank: number | null
  bay_position: number | null
  wrap_id?: string | null
  brand_code?: string | null
  fitness_ok: boolean | null
  wo_blocking: boolean | null
  brand_deficit: number
  mileage_deviation: number
  cleaning_needed: boolean
  clean_type?: string | null
}

const fetchDashboardSummary = async (planDate: string | null): Promise<DashboardSummaryResponse> => {
  const params: Record<string, string | boolean> = {}
  if (planDate) {
    params.plan_date = planDate
  }
  const { data } = await axios.get(`${API_BASE_URL}/api/v1/dashboard/summary`, {
    params,
  })
  return data
}

const formatDate = (value?: string | null): string => {
  if (!value) return '—'
  return new Date(value).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

const titleCase = (value: string): string =>
  value.length ? value.charAt(0).toUpperCase() + value.slice(1) : value

export default function Dashboard() {
  const { planDate } = usePlanDate()
  const selectionKey = planDate ?? 'latest'
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-summary', selectionKey],
    queryFn: () => fetchDashboardSummary(planDate),
  })

  const latestCounts = data?.latest_plan?.counts ?? { active: 0, standby: 0, ibl: 0 }
  const planSummary = data?.plan_details?.summary ?? { active: 0, standby: 0, ibl: 0, total: 0 }
  const maintenance = data?.maintenance
  const branding = data?.branding
  const alerts = data?.alerts ?? []
  const recentPlans = data?.recent_plans ?? []

  const focusAreas = useMemo(() => {
    if (!data || !maintenance || !branding) {
      return [
        {
          title: 'Awaiting data',
          description: 'Seed the Supabase instance to explore live metrics.',
          icon: Target,
        },
      ]
    }

    return [
      {
        title: 'Branding recovery',
        description: `${branding.active_campaigns} active campaigns · ${branding.total_exposure_hours.toFixed(1)}h exposure over last ${branding.period_days} days`,
        icon: Target,
      },
      {
        title: 'Maintenance pressure',
        description: `${maintenance.critical_jobs} critical jobs · ${maintenance.total_open_jobs} total open`,
        icon: ClipboardList,
      },
      {
        title: 'Fleet availability',
        description: `${data.fleet.availability.available_trains} ready trains · ${data.fleet.availability.availability_rate}% availability`,
        icon: TrendingUp,
      },
    ]
  }, [data, maintenance, branding])

  const dateRange = data?.data_window
  const startDate = dateRange?.start ? new Date(dateRange.start) : null
  const endDate = dateRange?.end ? new Date(dateRange.end) : null
  const dayCount = startDate && endDate
    ? Math.max(1, Math.round((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)) + 1)
    : null

  const dataCoverage = [
    {
      label: 'Synthetic days',
      value: dayCount ? String(dayCount) : '—',
      footnote: startDate && endDate ? `${formatDate(dateRange?.start)} – ${formatDate(dateRange?.end)}` : 'Seed data range',
    },
    {
      label: 'Trains simulated',
      value: String(data?.fleet?.total_trains ?? 0),
      footnote: 'Roster tracked in Supabase',
    },
    {
      label: 'Alerts logged',
      value: String(alerts.length),
      footnote: 'Last 6 alerts shown',
    },
  ]

  const stats = [
    {
      name: 'Active trains',
      value: latestCounts.active,
      change: 'Target band: 7 – 9',
      changeType: latestCounts.active >= 7 ? 'increase' : 'warning' as const,
      icon: Activity,
    },
    {
      name: 'Standby reserve',
      value: latestCounts.standby,
      change: 'Minimum reserve: 5',
      changeType: latestCounts.standby >= 5 ? 'neutral' : 'warning' as const,
      icon: Users,
    },
    {
      name: 'IBL jobs',
      value: latestCounts.ibl,
      change: `${maintenance?.critical_jobs ?? 0} critical tasks`,
      changeType: (maintenance?.critical_jobs ?? 0) > 0 ? 'warning' : 'neutral' as const,
      icon: Clock,
    },
    {
      name: 'Availability',
      value: `${data?.fleet?.availability?.availability_rate?.toFixed(1) ?? '0'}%`,
      change: `${data?.fleet?.availability?.available_trains ?? 0} trains ready`,
      changeType: 'success' as const,
      icon: CheckCircle,
    },
  ]

  if (isLoading) {
    return (
      <Layout>
        <div className="space-y-10 text-white">
          <div className="h-44 rounded-3xl bg-white/10 animate-pulse" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div key={idx} className="h-28 rounded-3xl bg-white/10 animate-pulse" />
            ))}
          </div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="h-60 rounded-3xl bg-white/10 animate-pulse" />
            <div className="h-60 rounded-3xl bg-white/10 animate-pulse" />
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-10 text-white">
        <Card className="border-white/15 bg-white/10">
          <CardContent className="px-6 py-8 sm:px-10">
            <div className="flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
              <div className="max-w-xl space-y-5">
                <Badge variant="info" className="uppercase tracking-[0.3em] text-[11px] text-white">Live dataset</Badge>
                <h1 className="text-3xl font-semibold leading-snug text-white">
                  Fleet snapshot and readiness for tonight&apos;s induction window
                </h1>
                <p className="text-sm leading-relaxed text-white/70">
                  Monitor capacity, IBL pressure, and sponsorship exposure. Jump into the plan board to adjust
                  assignments or inspect the overnight cleaning run.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Link
                    to="/planboard"
                    className="inline-flex items-center rounded-full bg-sky-500/90 px-4 py-2 text-sm font-semibold text-white shadow-[0_20px_45px_-25px_rgba(14,165,233,0.7)] transition hover:bg-sky-400/90"
                  >
                    Open plan board
                  </Link>
                  <Link
                    to="/ibl-gantt"
                    className="inline-flex items-center rounded-full border border-white/25 bg-white/15 px-4 py-2 text-sm font-medium text-white/90 transition hover:bg-white/25"
                  >
                    Review IBL schedule
                  </Link>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm text-white/70">
                <div>
                  <p className="uppercase tracking-[0.3em] text-[10px] text-white/50">Plan date</p>
                  <p className="mt-1 text-lg font-semibold text-white">{formatDate(data?.plan_details?.plan_date)}</p>
                </div>
                <div>
                  <p className="uppercase tracking-[0.3em] text-[10px] text-white/50">Data window</p>
                  <p className="mt-1 text-lg font-semibold text-white">
                    {startDate && endDate ? `${formatDate(dateRange?.start)} — ${formatDate(dateRange?.end)}` : 'Seed required'}
                  </p>
                </div>
                <div>
                  <p className="uppercase tracking-[0.3em] text-[10px] text-white/50">Plan window</p>
                  <p className="mt-1 text-lg font-semibold text-white">21:00 – 05:30 IST</p>
                </div>
                <div>
                  <p className="uppercase tracking-[0.3em] text-[10px] text-white/50">Last refresh</p>
                  <p className="mt-1 text-lg font-semibold text-white">Auto-sync on demand</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.name} className="border-white/10 bg-white/8">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="text-sm font-medium text-white/70">{stat.name}</CardTitle>
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/15 text-white">
                  <stat.icon className="h-5 w-5" />
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="text-3xl font-semibold text-white">{stat.value}</div>
                <p className={`text-xs font-medium ${
                  stat.changeType === 'increase'
                    ? 'text-emerald-200'
                    : stat.changeType === 'warning'
                    ? 'text-amber-200'
                    : stat.changeType === 'success'
                    ? 'text-emerald-200'
                    : 'text-white/60'
                }`}>
                  {stat.change}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="border-white/12 bg-white/8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-white">
                <Calendar className="h-5 w-5 text-sky-200" />
                Tonight&apos;s plan snapshot
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-3 gap-4 text-center text-white">
                <div>
                  <div className="text-2xl font-semibold text-emerald-200">{planSummary.active}</div>
                  <div className="text-xs uppercase tracking-[0.25em] text-white/60">Active</div>
                </div>
                <div>
                  <div className="text-2xl font-semibold text-sky-200">{planSummary.standby}</div>
                  <div className="text-xs uppercase tracking-[0.25em] text-white/60">Standby</div>
                </div>
                <div>
                  <div className="text-2xl font-semibold text-amber-200">{planSummary.ibl}</div>
                  <div className="text-xs uppercase tracking-[0.25em] text-white/60">IBL</div>
                </div>
              </div>
              <div className="rounded-2xl border border-white/15 bg-white/10 p-4 text-sm text-white/75">
                <div className="flex items-center justify-between">
                  <span>Fleet availability</span>
                  <Badge variant="success">
                    {data?.fleet?.availability?.availability_rate?.toFixed(1) ?? '0'}%
                  </Badge>
                </div>
                <p className="mt-2 text-xs text-white/60">
                  Based on active and standby trains with valid multi-department fitness coverage.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/12 bg-white/8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-white">
                <AlertTriangle className="h-5 w-5 text-amber-300" />
                Latest alerts
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {alerts.slice(0, 3).map((alert) => (
                <div
                  key={alert.alert_id}
                  className="flex items-start gap-3 rounded-2xl border border-white/15 bg-white/8 p-3 text-sm text-white/80"
                >
                  <Badge variant={alert.severity === 'critical' ? 'danger' : alert.severity === 'warning' ? 'warning' : 'info'}>
                    {titleCase(alert.severity)}
                  </Badge>
                  <div>
                    <div className="font-medium text-white">{alert.message}</div>
                    <div className="text-[11px] text-white/60">{formatDate(alert.plan_date)}</div>
                  </div>
                </div>
              ))}
              {!alerts.length && (
                <p className="text-sm text-white/60">No alerts logged for the seed dataset.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {focusAreas.map((focus) => (
            <Card key={focus.title} className="border-white/10 bg-white/8">
              <CardContent className="space-y-4">
                <div className="flex items-center gap-2 text-sm font-medium text-white/60">
                  <focus.icon className="h-4 w-4 text-white/70" />
                  Operational focus
                </div>
                <h3 className="text-lg font-semibold text-white">{focus.title}</h3>
                <p className="text-sm leading-relaxed text-white/70">{focus.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="border-white/12 bg-white/8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-white">
                <TrendingUp className="h-5 w-5 text-sky-200" />
                Recent plans
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {recentPlans.map((plan) => (
                <div
                  key={plan.plan_id}
                  className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-white/15 bg-white/8 px-4 py-3 text-sm"
                >
                  <div className="flex items-center gap-3">
                    <div className="font-medium text-white">{formatDate(plan.plan_date)}</div>
                    <Badge variant={plan.status === 'completed' ? 'success' : 'secondary'}>
                      {titleCase(plan.status)}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-white/70">
                    <div className="flex items-center gap-1">
                      <Activity className="h-4 w-4 text-emerald-200" />
                      {plan.active_count}
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="h-4 w-4 text-sky-200" />
                      {plan.standby_count}
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4 text-amber-200" />
                      {plan.ibl_count}
                    </div>
                  </div>
                </div>
              ))}
              {!recentPlans.length && (
                <p className="text-sm text-white/60">Plan history not available yet.</p>
              )}
            </CardContent>
          </Card>

          <Card className="border-white/12 bg-white/8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-white">
                <Sparkles className="h-5 w-5 text-sky-200" />
                Dataset coverage
              </CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {dataCoverage.map((item) => (
                <div
                  key={item.label}
                  className="rounded-2xl border border-white/15 bg-white/8 p-4 text-center"
                >
                  <p className="text-xs uppercase tracking-[0.25em] text-white/60">{item.label}</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{item.value}</p>
                  <p className="text-xs text-white/60">{item.footnote}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  )
}
