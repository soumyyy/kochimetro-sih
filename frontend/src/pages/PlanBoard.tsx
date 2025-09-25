import React, { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import Layout from '../components/Layout'
import { Card, CardContent } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import {
  Activity,
  Users,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Play,
  Settings,
} from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

interface PlanBoardResponse {
  plan_id: string
  plan_date: string
  status: string
  summary: {
    active: number
    standby: number
    ibl: number
    total: number
  }
  items: PlanItem[]
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

const fetchLatestPlan = async (): Promise<PlanBoardResponse> => {
  const { data } = await axios.get(`${API_BASE_URL}/api/v1/plans/latest`)
  return data
}

const statusConfig: Record<PlanItem['decision'], { color: string; icon: typeof Activity }> = {
  active: { color: 'bg-emerald-400/20 text-emerald-100', icon: Activity },
  standby: { color: 'bg-sky-400/20 text-sky-100', icon: Users },
  ibl: { color: 'bg-amber-400/25 text-amber-100', icon: Clock },
}

const priorityStyles: Record<PlanItem['priority'], string> = {
  high: 'text-rose-200',
  medium: 'text-amber-200',
  low: 'text-white/60',
}

const formatPlanDate = (iso?: string): string =>
  iso ? new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : '—'

export default function PlanBoard() {
  const { data, isLoading } = useQuery({ queryKey: ['latest-plan'], queryFn: fetchLatestPlan })

  const items = data?.items ?? []

  const columns = useMemo(
    () => ({
      active: items.filter((item) => item.decision === 'active'),
      standby: items.filter((item) => item.decision === 'standby'),
      ibl: items.filter((item) => item.decision === 'ibl'),
    }),
    [items],
  )

  if (isLoading) {
    return (
      <Layout>
        <div className="space-y-10 text-white">
          <div className="h-10 w-48 rounded-full bg-white/10 animate-pulse" />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div key={idx} className="h-24 rounded-3xl bg-white/10 animate-pulse" />
            ))}
          </div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, idx) => (
              <div key={idx} className="min-h-[360px] rounded-3xl bg-white/10 animate-pulse" />
            ))}
          </div>
        </div>
      </Layout>
    )
  }

  if (!data) {
    return (
      <Layout>
        <div className="rounded-3xl border border-white/15 bg-white/10 p-8 text-sm text-white/70 backdrop-blur-xl">
          No plans found. Seed the Supabase database and refresh.
        </div>
      </Layout>
    )
  }

  const planDateLabel = formatPlanDate(data.plan_date)

  return (
    <Layout>
      <div className="space-y-10 text-white">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-white">Plan board</h1>
            <p className="mt-2 text-sm text-white/70">
              Latest plan for <span className="font-medium text-white">{planDateLabel}</span>
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button className="inline-flex items-center rounded-full border border-white/20 bg-white/15 px-3.5 py-1.5 text-sm font-medium text-white/90 transition hover:bg-white/25">
              <Settings className="mr-2 h-4 w-4" />
              Weights
            </button>
            <button className="inline-flex items-center rounded-full bg-sky-500/90 px-3.5 py-1.5 text-sm font-semibold text-white shadow-[0_20px_45px_-25px_rgba(14,165,233,0.7)] transition hover:bg-sky-400/90">
              <Play className="mr-2 h-4 w-4" />
              Run optimisation
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <SummaryCard label="Active (target 7–9)" value={data.summary.active} accent="text-emerald-200" />
          <SummaryCard label="Standby reserve" value={data.summary.standby} accent="text-sky-200" />
          <SummaryCard label="IBL assignments" value={data.summary.ibl} accent="text-amber-200" />
          <SummaryCard label="Fleet tracked" value={data.summary.total} accent="text-white" />
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <Column title={`Active (${columns.active.length})`} icon={Activity} colour="text-emerald-200">
            {columns.active.map((item) => (
              <PlanCard key={item.train_id} item={item} />
            ))}
          </Column>
          <Column title={`Standby (${columns.standby.length})`} icon={Users} colour="text-sky-200">
            {columns.standby.map((item) => (
              <PlanCard key={item.train_id} item={item} />
            ))}
          </Column>
          <Column title={`IBL (${columns.ibl.length})`} icon={Clock} colour="text-amber-200">
            {columns.ibl.map((item) => (
              <PlanCard key={item.train_id} item={item} />
            ))}
          </Column>
        </div>
      </div>
    </Layout>
  )
}

function SummaryCard({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <Card className="border-white/12 bg-white/8">
      <CardContent className="p-4">
        <div className={`text-2xl font-semibold ${accent}`}>{value}</div>
        <div className="text-sm text-white/70">{label}</div>
      </CardContent>
    </Card>
  )
}

function Column({
  title,
  icon: Icon,
  colour,
  children,
}: {
  title: string
  icon: typeof Activity
  colour: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-4">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
        <Icon className={`h-5 w-5 ${colour}`} />
        {title}
      </h2>
      <div className="space-y-3">
        {React.Children.count(children) > 0 ? (
          children
        ) : (
          <div className="rounded-xl border border-dashed border-white/25 bg-white/5 p-4 text-sm text-white/60">
            No trains currently assigned
          </div>
        )}
      </div>
    </div>
  )
}

function PlanCard({ item }: { item: PlanItem }) {
  const StatusIcon = statusConfig[item.decision].icon
  const statusColour = statusConfig[item.decision].color
  const fitnessOk = item.fitness_ok ?? false
  const woBlocking = item.wo_blocking ?? false

  return (
    <Card className="border-white/12 bg-white/10 transition hover:bg-white/15">
      <CardContent className="space-y-3 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-white">{item.train_id}</h3>
            <Badge className={statusColour}>
              <StatusIcon className="mr-1 h-3 w-3" />
              {item.decision.toUpperCase()}
            </Badge>
            <span className={`text-xs font-medium ${priorityStyles[item.priority]}`}>
              {item.priority.toUpperCase()}
            </span>
          </div>
          {item.bay_position != null && (
            <Badge variant="secondary">Bay {item.bay_position.toString().padStart(2, '0')}</Badge>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs text-white/70">
          <div className="flex items-center gap-2">
            {fitnessOk ? (
              <CheckCircle className="h-4 w-4 text-emerald-300" />
            ) : (
              <XCircle className="h-4 w-4 text-rose-300" />
            )}
            <span>Fitness</span>
          </div>
          <div className="flex items-center gap-2">
            {woBlocking ? (
              <AlertTriangle className="h-4 w-4 text-amber-300" />
            ) : (
              <CheckCircle className="h-4 w-4 text-emerald-300" />
            )}
            <span>Work orders</span>
          </div>
          <div className="text-white/70">
            Brand Δ: {item.brand_deficit.toFixed(1)}h
          </div>
          <div className={item.mileage_deviation > 0 ? 'text-rose-200' : 'text-sky-200'}>
            Mileage: {item.mileage_deviation > 0 ? '+' : ''}
            {item.mileage_deviation.toFixed(0)} km
          </div>
        </div>

        {item.cleaning_needed && (
          <div className="rounded-lg bg-amber-400/20 px-3 py-2 text-xs text-amber-100">
            🧹 Cleaning scheduled ({item.clean_type ?? 'IBL'})
          </div>
        )}
      </CardContent>
    </Card>
  )
}
