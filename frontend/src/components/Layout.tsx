
import type { ChangeEvent, ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import {
  LayoutDashboard,
  Calendar,
  MapPin,
  BarChart3,
  Sparkles,
  Clock
} from 'lucide-react'
import { usePlanDate } from '../context/PlanDateContext'
import { Badge } from './ui/badge'

interface LayoutProps {
  children: ReactNode
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, blurb: 'Fleet pulse' },
  { name: 'Plan Board', href: '/planboard', icon: Calendar, blurb: 'Assignments & overrides' },
  { name: 'IBL Gantt', href: '/ibl-gantt', icon: MapPin, blurb: 'Night cleaning schedule' },
  { name: 'Depot View', href: '/depot', icon: MapPin, blurb: 'Bay occupancy' },
  { name: 'Sponsors', href: '/sponsors', icon: BarChart3, blurb: 'Brand exposure' },
]

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

interface PlanWindowMeta {
  windowLabel: string
  lastRefresh: string
  datasetRange: string
  planDate: string | null
}

interface PlanRangeResponse {
  start?: string | null
  end?: string | null
}

interface DashboardMetaResponse {
  latest_plan: {
    plan_id: string | null
    plan_date: string | null
  } | null
  data_window: PlanRangeResponse | null
}

const fetchPlanWindowMeta = async (planDate: string | null): Promise<PlanWindowMeta> => {
  try {
    const params: Record<string, string | boolean> = { include_details: false }
    if (planDate) {
      params.plan_date = planDate
    }

    const { data } = await axios.get<DashboardMetaResponse>(`${API_BASE_URL}/api/v1/dashboard/summary`, {
      params,
    })

    const planDateResponse = data.latest_plan?.plan_date
    const range = data.data_window ?? {}
    const start = range.start ? new Date(range.start) : null
    const end = range.end ? new Date(range.end) : null

    const dateFormatter = Intl.DateTimeFormat(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })

    const datasetRange = start && end
      ? `${dateFormatter.format(start)} – ${dateFormatter.format(end)}`
      : 'Seed data range'

    return {
      windowLabel: planDateResponse ? `Plan for ${dateFormatter.format(new Date(planDateResponse))}` : 'Latest plan snapshot',
      lastRefresh: new Date().toLocaleString(),
      datasetRange,
      planDate: planDateResponse ?? null,
    }
  } catch (error) {
    return {
      windowLabel: 'Latest plan snapshot',
      lastRefresh: new Date().toLocaleString(),
      datasetRange: 'Seed data range',
      planDate: null,
    }
  }
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const { planDate, setPlanDate, options, isLoadingOptions, latestPlanDate } = usePlanDate()
  const selectionKey = planDate ?? 'latest'
  const { data: planMeta } = useQuery({
    queryKey: ['layout-plan-meta', selectionKey],
    queryFn: () => fetchPlanWindowMeta(planDate),
    staleTime: 60 * 1000,
  })

  const windowLabel = planMeta?.windowLabel ?? 'Latest plan snapshot'
  const lastRefresh = planMeta?.lastRefresh ?? new Date().toLocaleString()
  const datasetRange = planMeta?.datasetRange ?? 'Seed data range'
  const effectivePlanDate = planMeta?.planDate ?? latestPlanDate

  const handlePlanDateChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const next = event.target.value
    if (next === '__custom') {
      return
    }
    setPlanDate(next ? next : null)
  }

  const handlePlanDateInput = (event: ChangeEvent<HTMLInputElement>) => {
    const next = event.target.value
    setPlanDate(next ? next : null)
  }

  const clearPlanDate = () => setPlanDate(null)

  const formattedSelectedDate = effectivePlanDate
    ? new Date(effectivePlanDate).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : null

  const minPlanDate = options.length ? options[options.length - 1].value : undefined
  const maxPlanDate = latestPlanDate ?? options[0]?.value
  const isCustomDate = planDate !== null && !options.some((option) => option.value === planDate)

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-50">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.18),transparent_55%),radial-gradient(circle_at_80%_10%,rgba(14,165,233,0.12),transparent_50%),linear-gradient(180deg,rgba(15,23,42,0.6)_0%,rgba(15,23,42,0.2)_45%,rgba(15,23,42,0.6)_100%)]"
        aria-hidden="true"
      />
      <div className="absolute inset-0 bg-gradient-to-b from-white/5 via-transparent to-white/10" aria-hidden="true" />

      <div className="relative z-10 flex min-h-screen flex-col px-4 pt-8 pb-36 sm:px-6 lg:px-12">
        <header className="mx-auto w-full max-w-6xl rounded-3xl border border-white/12 bg-white/10 px-5 py-5 shadow-[0_24px_65px_-36px_rgba(15,23,42,0.9)] backdrop-blur-2xl">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/12">
                <Sparkles className="h-5 w-5 text-sky-200" />
              </div>
              <div className="space-y-1">
                <p className="text-xs font-semibold uppercase tracking-[0.4em] text-white/60">Plan window</p>
                <p className="text-base font-semibold text-white">{windowLabel}</p>
                <p className="text-xs text-white/65">
                  {formattedSelectedDate ? `Selected ${formattedSelectedDate}` : 'Latest available plan'} · {datasetRange}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary" className="flex items-center gap-2 text-[11px] uppercase tracking-wide">
                <Clock className="h-3.5 w-3.5 text-sky-200" />
                Last sync {lastRefresh}
              </Badge>
            </div>
          </div>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap items-center gap-2">
              <select
                className="h-10 min-w-[200px] rounded-2xl border border-white/30 bg-white/85 px-3 text-sm font-semibold text-slate-900 shadow-sm transition focus:border-sky-400/70 focus:outline-none"
                onChange={handlePlanDateChange}
                value={isCustomDate ? '__custom' : planDate ?? ''}
                disabled={isLoadingOptions}
              >
                <option value="">Latest plan</option>
                {options.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
                {planDate && isCustomDate && (
                  <option value="__custom">Custom date</option>
                )}
              </select>
              <input
                type="date"
                className="h-10 rounded-2xl border border-white/30 bg-white/85 px-3 text-sm font-semibold text-slate-900 shadow-sm transition focus:border-sky-400/70 focus:outline-none"
                value={planDate ?? ''}
                onChange={handlePlanDateInput}
                min={minPlanDate}
                max={maxPlanDate}
              />
            </div>
            <button
              type="button"
              onClick={clearPlanDate}
              className="inline-flex h-10 items-center rounded-2xl border border-white/15 bg-white/10 px-3 text-sm font-medium text-white/80 transition hover:bg-white/20"
            >
              Use latest
            </button>
          </div>
        </header>

        <main className="mx-auto mt-10 w-full max-w-6xl flex-1 pb-10">
          <div className="space-y-10">
            {children}
          </div>
        </main>
      </div>

      <nav className="fixed bottom-7 left-1/2 z-30 flex w-[min(90%,680px)] -translate-x-1/2 items-center justify-between gap-2 rounded-full border border-white/25 bg-white/15 px-3 py-3 backdrop-blur-2xl shadow-[0_24px_80px_-36px_rgba(15,23,42,0.9)]">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`flex flex-1 items-center justify-center gap-2 rounded-full px-3 py-2 text-sm transition-all ${
                isActive
                  ? 'bg-white/90 text-slate-900 shadow-[0_12px_30px_-18px_rgba(15,23,42,0.8)]'
                  : 'text-white/80 hover:bg-white/25 hover:text-white'
              }`}
            >
              <item.icon className={`h-4 w-4 ${isActive ? 'text-slate-900' : 'text-white/70'}`} />
              <span className="hidden text-sm font-medium sm:inline-block">{item.name}</span>
            </Link>
          )
        })}
      </nav>

      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-20 h-36 bg-gradient-to-t from-slate-950 via-slate-950/70 to-transparent" aria-hidden="true" />
    </div>
  )
}
