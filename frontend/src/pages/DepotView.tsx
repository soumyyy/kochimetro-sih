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

const fetchDepotInfo = async (): Promise<DepotSummaryResponse> => {
  const { data } = await axios.get(`${API_BASE_URL}/api/v1/ref/depot`)
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
      return 'bg-emerald-100 text-emerald-800 border-emerald-200'
    case 'available':
      return 'bg-slate-100 text-slate-700 border-slate-200'
    case 'inactive':
      return 'bg-amber-100 text-amber-800 border-amber-200'
    default:
      return 'bg-slate-100 text-slate-700 border-slate-200'
  }
}

export default function DepotView() {
  const { data, isLoading, error } = useQuery({ queryKey: ['depot-info'], queryFn: fetchDepotInfo })

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
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-800">
          Failed to load depot data. Please refresh once the API is reachable.
        </div>
      </Layout>
    )
  }

  if (isLoading) {
    return (
      <Layout>
        <div className="space-y-6">
          <div className="h-8 w-48 rounded bg-slate-200 animate-pulse" />
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
          No depot information available. Seed the database and try again.
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Depot View</h1>
            <p className="mt-1 text-sm text-slate-600">
              Stabling and turnout overview · Plan date {formatDate(data.summary.plan_date)}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant="info">Assignments {data.summary.assignments_available ? 'available' : 'pending'}</Badge>
            <Badge variant="outline">Depots: {depots.length}</Badge>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <SummaryCard
            label="Occupied bays"
            value={occupiedBays}
            icon={MapPin}
            accent="text-emerald-600"
          />
          <SummaryCard
            label="Available bays"
            value={availableBays}
            icon={CheckCircle}
            accent="text-blue-600"
          />
          <SummaryCard
            label="Inactive bays"
            value={inactiveBays}
            icon={AlertTriangle}
            accent="text-amber-600"
          />
          <SummaryCard
            label="Total bays"
            value={bays.length}
            icon={Warehouse}
            accent="text-slate-700"
          />
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Bay status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {bays.map((bay) => {
                  const status = bayStatus(bay)
                  return (
                    <div
                      key={bay.bay_id}
                      className={`flex items-center justify-between rounded-xl border px-4 py-3 ${statusBadgeClass(status)}`}
                    >
                      <div>
                        <div className="text-sm font-semibold text-slate-900">{bay.bay_id}</div>
                        <div className="text-xs text-slate-600">
                          Position {bay.position_idx} · {bay.electrified ? 'Electrified' : 'Non-electrified'} ·
                          Access {bay.access_time_min} min
                        </div>
                        {bay.plan_assignments.length > 0 && (
                          <div className="text-xs text-slate-500">
                            Planned: {bay.plan_assignments.map((assignment) => assignment.train_id).join(', ')}
                          </div>
                        )}
                      </div>
                      <div className="text-right text-xs text-slate-600">
                        {bay.current_train ? (
                          <div>
                            <span className="font-medium text-slate-800">{bay.current_train}</span>
                            <div className="text-[11px] uppercase tracking-wide text-slate-500">
                              {bay.current_train_status ?? 'unknown'}
                            </div>
                          </div>
                        ) : (
                          <div className="text-slate-500">No train assigned</div>
                        )}
                        {bay.next_turnout_rank !== null && (
                          <div className="text-[11px] text-slate-500">Turnout #{bay.next_turnout_rank}</div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Navigation className="h-5 w-5" />
                Turnout schedule
              </CardTitle>
            </CardHeader>
            <CardContent>
              {turnoutSchedule.length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-10 text-center text-sm text-slate-500">
                  No turnout order available for this plan.
                </div>
              ) : (
                <div className="space-y-3">
                  {turnoutSchedule.map((item) => (
                    <div
                      key={`${item.train_id}-${item.turnout_rank}`}
                      className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm"
                    >
                      <div className="font-medium text-slate-800">{item.train_id}</div>
                      <div className="text-xs text-slate-500">Bay {item.bay_id}</div>
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
