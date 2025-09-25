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

const fetchDashboardSummary = async (): Promise<DashboardSummaryResponse> => {
  const { data } = await axios.get(`${API_BASE_URL}/api/v1/dashboard/summary`)
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
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchDashboardSummary,
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
        <div className="space-y-8">
          <div className="h-40 rounded-3xl bg-slate-100 animate-pulse" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div key={idx} className="h-32 rounded-2xl bg-slate-100 animate-pulse" />
            ))}
          </div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="h-56 rounded-2xl bg-slate-100 animate-pulse" />
            <div className="h-56 rounded-2xl bg-slate-100 animate-pulse" />
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-8">
        <Card className="rounded-3xl border border-slate-200/60 bg-white/80 shadow-xl backdrop-blur">
          <CardContent className="px-6 py-8 sm:px-10 sm:py-9">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div className="max-w-xl space-y-4">
                <Badge variant="info" className="uppercase tracking-wide text-[11px]">Synthetic dataset</Badge>
                <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
                  Fleet snapshot and plan readiness for tonight&apos;s induction run
                </h1>
                <p className="text-sm leading-relaxed text-slate-600">
                  Monitor active capacity, IBL pressure, and sponsorship exposure derived from the
                  seeded Supabase dataset. Use the quick links to adjust assignments or inspect the
                  overnight cleaning window.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Link
                    to="/planboard"
                    className="inline-flex items-center rounded-full bg-blue-600 px-3.5 py-1.5 text-sm font-semibold text-white shadow-[0_18px_35px_-20px_rgba(37,99,235,0.75)] transition hover:bg-blue-700"
                  >
                    Open plan board
                  </Link>
                  <Link
                    to="/ibl-gantt"
                    className="inline-flex items-center rounded-full border border-slate-200 bg-slate-100/80 px-3.5 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
                  >
                    Review IBL schedule
                  </Link>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm text-slate-600">
                <div>
                  <p className="uppercase tracking-[0.18em] text-[11px] text-slate-500">Plan date</p>
                  <p className="mt-1 font-semibold text-slate-800">{formatDate(data?.plan_details?.plan_date)}</p>
                </div>
                <div>
                  <p className="uppercase tracking-[0.18em] text-[11px] text-slate-500">Dataset range</p>
                  <p className="mt-1 font-semibold text-slate-800">
                    {startDate && endDate ? `${formatDate(dateRange?.start)} – ${formatDate(dateRange?.end)}` : 'Seed required'}
                  </p>
                </div>
                <div>
                  <p className="uppercase tracking-[0.18em] text-[11px] text-slate-500">Plan window</p>
                  <p className="mt-1 font-semibold text-slate-800">21:00 – 05:30 IST</p>
                </div>
                <div>
                  <p className="uppercase tracking-[0.18em] text-[11px] text-slate-500">Last refresh</p>
                  <p className="mt-1 font-semibold text-slate-800">Auto-refresh on request</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {stats.map((stat) => (
            <Card
              key={stat.name}
              className="rounded-2xl border border-slate-200/60 bg-white/90 shadow-sm backdrop-blur"
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="text-sm font-medium text-slate-600">
                  {stat.name}
                </CardTitle>
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-50 text-blue-600">
                  <stat.icon className="h-4 w-4" />
                </div>
              </CardHeader>
              <CardContent className="space-y-2 p-6 pt-0">
                <div className="text-3xl font-semibold text-slate-900">{stat.value}</div>
                <p className={`text-xs font-medium ${
                  stat.changeType === 'increase'
                    ? 'text-green-600'
                    : stat.changeType === 'warning'
                    ? 'text-amber-600'
                    : stat.changeType === 'success'
                    ? 'text-green-600'
                    : 'text-slate-500'
                }`}>
                  {stat.change}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="rounded-2xl border border-slate-200/60 bg-white/90 shadow-sm backdrop-blur">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-slate-800">
                <Calendar className="h-5 w-5 text-blue-600" />
                Tonight&apos;s plan snapshot
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-semibold text-emerald-600">{planSummary.active}</div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Active</div>
                </div>
                <div>
                  <div className="text-2xl font-semibold text-blue-600">{planSummary.standby}</div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Standby</div>
                </div>
                <div>
                  <div className="text-2xl font-semibold text-amber-600">{planSummary.ibl}</div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">IBL jobs</div>
                </div>
              </div>
              <div className="rounded-xl border border-slate-200/70 bg-slate-50 p-4 text-sm text-slate-600">
                <div className="flex items-center justify-between">
                  <span>Fleet availability</span>
                  <Badge variant="success">
                    {data?.fleet?.availability?.availability_rate?.toFixed(1) ?? '0'}%
                  </Badge>
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  Based on availability of active and standby trains with valid fitness certificates.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-2xl border border-slate-200/60 bg-white/90 shadow-sm backdrop-blur">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-slate-800">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
                Latest alerts
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {alerts.slice(0, 3).map((alert) => (
                <div
                  key={alert.alert_id}
                  className="flex items-start gap-3 rounded-xl border border-slate-200/80 bg-slate-50 p-3 text-sm text-slate-700"
                >
                  <Badge variant={alert.severity === 'critical' ? 'danger' : alert.severity === 'warning' ? 'warning' : 'info'}>
                    {titleCase(alert.severity)}
                  </Badge>
                  <div>
                    <div className="font-medium text-slate-800">{alert.message}</div>
                    <div className="text-[11px] text-slate-500">{formatDate(alert.plan_date)}</div>
                  </div>
                </div>
              ))}
              {!alerts.length && (
                <p className="text-sm text-slate-500">No alerts logged for the seed dataset.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {focusAreas.map((focus) => (
            <Card
              key={focus.title}
              className="rounded-2xl border border-slate-200/60 bg-white/90 shadow-sm backdrop-blur"
            >
              <CardContent className="space-y-3 p-6">
                <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
                  <focus.icon className="h-4 w-4 text-blue-600" />
                  Operational focus
                </div>
                <h3 className="text-base font-semibold text-slate-800">{focus.title}</h3>
                <p className="text-sm leading-relaxed text-slate-600">{focus.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="rounded-2xl border border-slate-200/60 bg-white/90 shadow-sm backdrop-blur">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-slate-800">
                <TrendingUp className="h-5 w-5 text-blue-600" />
                Recent plans
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {recentPlans.map((plan) => (
                <div
                  key={plan.plan_id}
                  className="flex items-center justify-between rounded-2xl border border-slate-200/60 bg-white/90 p-4 text-sm"
                >
                  <div className="flex items-center gap-4">
                    <div className="font-medium text-slate-800">{formatDate(plan.plan_date)}</div>
                    <Badge variant={plan.status === 'completed' ? 'success' : 'default'}>
                      {plan.status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-5 text-slate-500">
                    <div className="flex items-center gap-1">
                      <Activity className="h-4 w-4 text-emerald-600" />
                      {plan.active_count}
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="h-4 w-4 text-blue-600" />
                      {plan.standby_count}
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4 text-amber-600" />
                      {plan.ibl_count}
                    </div>
                  </div>
                </div>
              ))}
              {!recentPlans.length && (
                <p className="text-sm text-slate-500">Plan history not available yet.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="rounded-2xl border border-slate-200/60 bg-white/90 shadow-sm backdrop-blur">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg text-slate-800">
              <Sparkles className="h-5 w-5 text-blue-600" />
              Dataset coverage
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {dataCoverage.map((item) => (
              <div
                key={item.label}
                className="rounded-2xl border border-slate-200/70 bg-white/90 p-4 text-center"
              >
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{item.label}</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">{item.value}</p>
                <p className="text-xs text-slate-500">{item.footnote}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
