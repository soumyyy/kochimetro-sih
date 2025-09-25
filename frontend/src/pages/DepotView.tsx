import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import Layout from '../components/Layout'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import {
  MapPin,
  Navigation,
  AlertTriangle,
  CheckCircle,
  Warehouse
} from 'lucide-react'
import { usePlanDate } from '../context/PlanDateContext'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

interface DepotSummaryResponse {
  summary: {
    plan_date: string | null
    total_depots: number
    total_bays: number
    occupied_bays: number
    assignments_available: boolean
  }
  depots: DepotInfo[]
  bays: BayInfo[]
  occupancy: OccupancySlice[]
  routes: Array<Record<string, unknown>>
  conflicts: Array<Record<string, unknown>>
}

interface DepotInfo {
  depot_id: string
  code: string | null
  name: string
  is_active: boolean
  bay_count: number
  active_bay_count: number
  occupied_bay_count: number
}

interface PlanAssignment {
  train_id: string
  decision: string
  turnout_rank: number | null
}

interface BayInfo {
  bay_id: string
  depot_id: string
  position_idx: number
  electrified: boolean
  length_m: number
  access_time_min: number
  is_active: boolean
  current_train: string | null
  current_train_status: string | null
  current_wrap_id: string | null
  next_turnout_rank: number | null
  plan_assignments: PlanAssignment[]
  occupancy: OccupancySlice[]
}

interface OccupancySlice {
  bay_id?: string
  train_id: string
  from_ts: string
  to_ts: string
  duration_hours: number
}

const fetchDepotInfo = async (planDate: string | null): Promise<DepotSummaryResponse> => {
  const params: Record<string, string | boolean> = {}
  if (planDate) {
    params.plan_date = planDate
  }
  const { data } = await axios.get(`${API_BASE_URL}/api/v1/ref/depot`, {
    params,
  })
  return data
}

const formatDate = (value: string | null | undefined): string => {
  if (!value) return '—'
  return new Date(value).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

const bayStatus = (bay: BayInfo): 'occupied' | 'available' | 'inactive' => {
  if (!bay.is_active) return 'inactive'
  return bay.current_train ? 'occupied' : 'available'
}

const statusBadgeClass = (status: 'occupied' | 'available' | 'inactive'): string => {
  switch (status) {
    case 'occupied':
      return 'border border-emerald-300/50 bg-emerald-400/20 text-emerald-100'
    case 'available':
      return 'border border-white/20 bg-white/10 text-white/80'
    case 'inactive':
      return 'border border-amber-300/40 bg-amber-400/20 text-amber-100'
    default:
      return 'border border-white/20 bg-white/10 text-white/80'
  }
}

export default function DepotView() {
  const { planDate } = usePlanDate()
  const selectionKey = planDate ?? 'latest'
  const { data, isLoading, error } = useQuery({
    queryKey: ['depot-info', selectionKey],
    queryFn: () => fetchDepotInfo(planDate),
  })

  const depots = data?.depots ?? []
  const bays = useMemo(
    () => (data?.bays ?? []).slice().sort((a, b) => a.position_idx - b.position_idx),
    [data?.bays],
  )

  const turnoutSchedule = useMemo(() => {
    if (!data?.bays) return []
    const assignments = data.bays.flatMap((bay) =>
      bay.plan_assignments
        .filter((assignment) => assignment.turnout_rank !== null)
        .map((assignment) => ({
          ...assignment,
          bay_id: bay.bay_id,
        })),
    )

    return assignments.sort((a, b) => (a.turnout_rank ?? 0) - (b.turnout_rank ?? 0))
  }, [data?.bays])

  const availableBays = bays.filter((bay) => bayStatus(bay) === 'available').length
  const occupiedBays = bays.filter((bay) => bayStatus(bay) === 'occupied').length
  const inactiveBays = bays.filter((bay) => bayStatus(bay) === 'inactive').length

  if (error) {
    return (
      <Layout>
        <div className="rounded-3xl border border-rose-300/40 bg-rose-500/20 p-6 text-sm text-rose-100 backdrop-blur-xl">
          Failed to load depot data. Please refresh once the API is reachable.
        </div>
      </Layout>
    )
  }

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
          No depot information available. Seed the database and try again.
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-10 text-white">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-white">Depot View</h1>
            <p className="mt-2 text-sm text-white/70">
              Stabling and turnout overview · Plan date {formatDate(data.summary.plan_date)}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant="info">Assignments {data.summary.assignments_available ? 'available' : 'pending'}</Badge>
            <Badge variant="secondary">Depots: {depots.length}</Badge>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <SummaryCard
            label="Occupied bays"
            value={occupiedBays}
            icon={MapPin}
            accent="text-emerald-200"
          />
          <SummaryCard
            label="Available bays"
            value={availableBays}
            icon={CheckCircle}
            accent="text-sky-200"
          />
          <SummaryCard
            label="Inactive bays"
            value={inactiveBays}
            icon={AlertTriangle}
            accent="text-amber-200"
          />
          <SummaryCard
            label="Total bays"
            value={bays.length}
            icon={Warehouse}
            accent="text-white"
          />
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="border-white/12 bg-white/8">
            <CardHeader>
              <CardTitle className="text-white">Bay status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {bays.map((bay) => {
                  const status = bayStatus(bay)
                  return (
                    <div
                      key={bay.bay_id}
                      className={`flex items-center justify-between rounded-xl px-4 py-3 ${statusBadgeClass(status)}`}
                    >
                      <div>
                        <div className="text-sm font-semibold text-white">{bay.bay_id}</div>
                        <div className="text-xs text-white/70">
                          Position {bay.position_idx} · {bay.electrified ? 'Electrified' : 'Non-electrified'} ·
                          Access {bay.access_time_min} min
                        </div>
                        {bay.plan_assignments.length > 0 && (
                          <div className="text-xs text-white/60">
                            Planned: {bay.plan_assignments.map((assignment) => assignment.train_id).join(', ')}
                          </div>
                        )}
                      </div>
                      <div className="text-right text-xs text-white/70">
                        {bay.current_train ? (
                          <div>
                            <span className="font-medium text-white">{bay.current_train}</span>
                            <div className="text-[11px] uppercase tracking-wide text-white/60">
                              {bay.current_train_status ?? 'unknown'}
                            </div>
                          </div>
                        ) : (
                          <div className="text-white/50">No train assigned</div>
                        )}
                        {bay.next_turnout_rank !== null && (
                          <div className="text-[11px] text-white/60">Turnout #{bay.next_turnout_rank}</div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/12 bg-white/8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Navigation className="h-5 w-5" />
                Turnout schedule
              </CardTitle>
            </CardHeader>
            <CardContent>
              {turnoutSchedule.length === 0 ? (
                <div className="rounded-xl border border-dashed border-white/25 bg-white/5 p-10 text-center text-sm text-white/60">
                  No turnout order available for this plan.
                </div>
              ) : (
                <div className="space-y-3">
                  {turnoutSchedule.map((item) => (
                    <div
                      key={`${item.train_id}-${item.turnout_rank}`}
                      className="flex items-center justify-between rounded-lg border border-white/15 bg-white/10 px-4 py-2 text-sm text-white/80"
                    >
                      <div className="font-medium text-white">{item.train_id}</div>
                      <div className="text-xs text-white/60">Bay {item.bay_id}</div>
                      <Badge variant="secondary">#{item.turnout_rank}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
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
  value: number
  icon: typeof MapPin
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
