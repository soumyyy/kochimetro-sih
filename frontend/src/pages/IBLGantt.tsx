import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import Layout from '../components/Layout'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import {
  ClipboardList,
  Clock,
  MapPin,
  TrainFront
} from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const SLOT_WIDTH_REM = 4
const SLOTS_PER_WINDOW = 18
const SLOT_MINUTES = 30
const LEFT_COLUMN_WIDTH_REM = 16

interface LatestPlanMeta {
  plan_id: string
  plan_date: string
  status: string
}

interface PlanDetailsResponse {
  plan_id: string
  plan_date: string
  status: string
  ibl_gantt: Array<IBLGanttSlot>
}

interface IBLGanttSlot {
  bay_id: string
  train_id: string
  from_ts: string
  to_ts: string
  job_type?: string
  assigned_crew?: string
  priority?: string
}

interface GanttJob {
  bay_id: string
  train_id: string
  start: Date
  end: Date
  durationHours: number
  startIndex: number
  endIndex: number
  jobType?: string
  assignedCrew?: string
  priority?: string
}

interface DepotReferenceResponse {
  depots: Array<{
    depot_id: string
    code?: string | null
    name: string
  }>
  bays: Array<{
    bay_id: string
    depot_id: string
    position_idx: number
    is_active: boolean
  }>
}

const fetchLatestPlanMeta = async (): Promise<LatestPlanMeta | null> => {
  try {
    const { data } = await axios.get(`${API_BASE_URL}/api/v1/plans/latest`, {
      params: { include_features: false },
    })
    return {
      plan_id: data.plan_id,
      plan_date: data.plan_date,
      status: data.status,
    }
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null
    }
    throw error
  }
}

const fetchPlanDetails = async (planId: string): Promise<PlanDetailsResponse> => {
  const { data } = await axios.get(`${API_BASE_URL}/api/v1/plans/${planId}`)
  return data
}

const fetchDepotReference = async (): Promise<DepotReferenceResponse> => {
  const { data } = await axios.get(`${API_BASE_URL}/api/v1/reference/depot`, {
    params: { include_occupancy: false },
  })
  return data
}

const formatTime = (date: Date): string =>
  date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })

const minutesBetween = (start: Date, end: Date): number =>
  (end.getTime() - start.getTime()) / (1000 * 60)

const abbreviatePlanId = (planId: string): string =>
  planId.length <= 12 ? planId : `${planId.slice(0, 8)}…${planId.slice(-4)}`

const toTitleCase = (value: string): string =>
  value
    .split(/[_\s-]+/g)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ')

const formatJobType = (jobType?: string): string => {
  if (!jobType) return 'Maintenance'
  const cleaned = jobType.trim()
  if (!cleaned) return 'Maintenance'
  return toTitleCase(cleaned)
}

type JobPalette = {
  barClass: string
  borderClass: string
  textClass: string
  dotClass: string
  badgeVariant: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'secondary'
}

const getJobPalette = (jobType?: string): JobPalette => {
  const normalized = jobType?.toLowerCase() ?? ''

  if (normalized.includes('clean')) {
    return {
      barClass: 'bg-emerald-400/20',
      borderClass: 'border-emerald-200/50',
      textClass: 'text-emerald-100',
      dotClass: 'bg-emerald-300/80',
      badgeVariant: 'success',
    }
  }

  if (normalized.includes('inspection')) {
    return {
      barClass: 'bg-amber-400/20',
      borderClass: 'border-amber-200/50',
      textClass: 'text-amber-100',
      dotClass: 'bg-amber-300/80',
      badgeVariant: 'warning',
    }
  }

  if (normalized.includes('branding')) {
    return {
      barClass: 'bg-fuchsia-400/20',
      borderClass: 'border-fuchsia-200/40',
      textClass: 'text-fuchsia-100',
      dotClass: 'bg-fuchsia-300/80',
      badgeVariant: 'secondary',
    }
  }

  return {
    barClass: 'bg-sky-400/20',
    borderClass: 'border-sky-200/40',
    textClass: 'text-sky-100',
    dotClass: 'bg-sky-300/80',
    badgeVariant: 'info',
  }
}

const getPriorityVariant = (priority?: string): JobPalette['badgeVariant'] => {
  const normalized = priority?.toLowerCase()
  switch (normalized) {
    case 'high':
      return 'danger'
    case 'low':
      return 'secondary'
    default:
      return 'warning'
  }
}

export default function IBLGantt() {
  const {
    data: planMeta,
    isLoading: metaLoading,
    error: metaError,
  } = useQuery({ queryKey: ['latest-plan-meta'], queryFn: fetchLatestPlanMeta })

  const planId = planMeta?.plan_id

  const {
    data: planDetails,
    isLoading: detailsLoading,
    error: detailsError,
  } = useQuery({
    queryKey: ['plan-details', planId],
    queryFn: () => fetchPlanDetails(planId!),
    enabled: Boolean(planId),
  })

  const { data: depotMeta } = useQuery({
    queryKey: ['depot-reference'],
    queryFn: fetchDepotReference,
  })

  const isLoading = metaLoading || (Boolean(planId) && detailsLoading)
  const queryError = (metaError ?? detailsError) ?? null

  const planDateIso = planDetails?.plan_date ?? planMeta?.plan_date ?? null
  const planStatus = planDetails?.status ?? planMeta?.status ?? 'unknown'

  const windowStart = useMemo(() => {
    if (planDateIso) {
      return new Date(`${planDateIso}T21:00:00`)
    }
    const firstSlot = planDetails?.ibl_gantt?.[0]
    if (firstSlot) {
      const start = new Date(firstSlot.from_ts)
      start.setHours(21, 0, 0, 0)
      return start
    }
    return null
  }, [planDateIso, planDetails?.ibl_gantt])

  const timeSlots = useMemo(() => {
    if (!windowStart) return []
    return Array.from({ length: SLOTS_PER_WINDOW }, (_, idx) => {
      const slotTime = new Date(windowStart.getTime() + idx * SLOT_MINUTES * 60 * 1000)
      return formatTime(slotTime)
    })
  }, [windowStart])

  const jobs: GanttJob[] = useMemo(() => {
    if (!windowStart || !planDetails?.ibl_gantt?.length) {
      return []
    }

    return planDetails.ibl_gantt
      .map((slot) => {
        const start = new Date(slot.from_ts)
        const end = new Date(slot.to_ts)
        const durationMinutes = minutesBetween(start, end)
        const startOffset = minutesBetween(windowStart, start)
        const endOffset = startOffset + durationMinutes

        const startIndex = Math.max(startOffset / SLOT_MINUTES, 0)
        const endIndex = Math.max(endOffset / SLOT_MINUTES, startIndex)

        return {
          bay_id: slot.bay_id,
          train_id: slot.train_id,
          start,
          end,
          durationHours: Math.max(durationMinutes / 60, 0),
          startIndex,
          endIndex,
          jobType: slot.job_type,
          assignedCrew: slot.assigned_crew,
          priority: slot.priority,
        }
      })
      .sort((a, b) => a.start.getTime() - b.start.getTime())
  }, [planDetails?.ibl_gantt, windowStart])

  const bayLabelLookup = useMemo(() => {
    if (!depotMeta?.bays?.length) return new Map<string, { label: string; depotLabel?: string | null }>()
    const depotLookup = new Map<string, { code?: string | null; name: string }>()
    depotMeta.depots?.forEach((depot) => {
      depotLookup.set(depot.depot_id, { code: depot.code, name: depot.name })
    })

    const entries = depotMeta.bays.reduce((acc, bay) => {
      if (!bay.is_active) return acc
      const depot = depotLookup.get(bay.depot_id)
      const depotLabel = depot?.code ?? depot?.name ?? 'Depot'
      acc.set(bay.bay_id, {
        label: `${depotLabel} Bay ${bay.position_idx}`,
        depotLabel,
      })
      return acc
    }, new Map<string, { label: string; depotLabel?: string | null }>())

    return entries
  }, [depotMeta])

  const uniqueBays = useMemo(() => new Set(jobs.map((job) => job.bay_id)).size, [jobs])
  const uniqueTrains = useMemo(() => new Set(jobs.map((job) => job.train_id)).size, [jobs])
  const totalHours = useMemo(
    () => jobs.reduce((sum, job) => sum + job.durationHours, 0),
    [jobs],
  )

  const jobTypeLegend = useMemo(
    () =>
      jobs.reduce<Array<{ label: string; palette: JobPalette }>>((acc, job) => {
        const label = formatJobType(job.jobType)
        if (acc.some((entry) => entry.label === label)) {
          return acc
        }
        return [...acc, { label, palette: getJobPalette(job.jobType) }]
      }, []),
    [jobs],
  )

  if (queryError) {
    let message = 'Failed to load IBL schedule'
    if (axios.isAxiosError(queryError)) {
      message = queryError.response?.data?.detail ?? queryError.message
    } else if (queryError instanceof Error) {
      message = queryError.message
    }

    return (
      <Layout>
        <div className="rounded-3xl border border-rose-300/40 bg-rose-500/20 p-6 text-sm text-rose-100 backdrop-blur-xl">
          {message}
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
          <div className="h-[480px] rounded-3xl bg-white/10 animate-pulse" />
        </div>
      </Layout>
    )
  }

  if (!planMeta || !planId) {
    return (
      <Layout>
        <div className="rounded-3xl border border-white/15 bg-white/10 p-8 text-sm text-white/70 backdrop-blur-xl">
          No plans found. Seed the database and refresh to view the IBL schedule.
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-10 text-white">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-white">IBL Gantt Chart</h1>
            <p className="mt-2 text-sm text-white/70">
              Night work schedule for {planDateIso ? new Date(planDateIso).toLocaleDateString() : 'upcoming plan'}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="info">Plan status: {planStatus}</Badge>
            {(planDetails?.plan_id ?? planMeta?.plan_id) && (
              <Badge variant="secondary">
                Plan ref: {abbreviatePlanId(planDetails?.plan_id ?? planMeta?.plan_id ?? '')}
              </Badge>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <SummaryCard
            label="Night jobs"
            value={jobs.length}
            icon={ClipboardList}
            accent="text-sky-200"
          />
          <SummaryCard
            label="Total hours"
            value={totalHours.toFixed(1)}
            icon={Clock}
            accent="text-emerald-200"
          />
          <SummaryCard
            label="Unique trains"
            value={uniqueTrains}
            icon={TrainFront}
            accent="text-indigo-200"
          />
          <SummaryCard
            label="Bays utilised"
            value={uniqueBays}
            icon={MapPin}
            accent="text-amber-200"
          />
        </div>

        <Card className="border-white/12 bg-white/8">
          <CardHeader>
            <CardTitle className="text-white">Maintenance schedule</CardTitle>
          </CardHeader>
          <CardContent>
            {jobs.length === 0 || !windowStart ? (
              <div className="rounded-xl border border-dashed border-white/25 bg-white/5 p-12 text-center text-sm text-white/60">
                No IBL occupancy recorded for this plan window.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <div className="min-w-full">
                  <div className="flex border-b border-white/15">
                    <div
                      className="flex-shrink-0 p-2 text-sm font-semibold text-white"
                      style={{ width: `${LEFT_COLUMN_WIDTH_REM}rem` }}
                    >
                      Bay &amp; train
                    </div>
                    {timeSlots.map((label, idx) => (
                      <div
                        key={label}
                        className={`flex-shrink-0 border-l border-white/10 p-2 text-center text-xs font-medium ${
                          idx % 2 === 1 ? 'bg-white/5 text-white/70' : 'text-white/60'
                        }`}
                        style={{ width: `${SLOT_WIDTH_REM}rem` }}
                      >
                        {label}
                      </div>
                    ))}
                  </div>

                  <div className="space-y-1">
                    {jobs.map((job) => {
                      const widthRem = Math.max(job.endIndex - job.startIndex, 0.5) * SLOT_WIDTH_REM
                      const leftRem = Math.max(job.startIndex, 0) * SLOT_WIDTH_REM
                      const bayLookup = bayLabelLookup.get(job.bay_id)
                      const bayLabel = bayLookup?.label ?? `Bay ${job.bay_id.slice(0, 6).toUpperCase()}`
                      const palette = getJobPalette(job.jobType)

                      return (
                        <div
                          key={`${job.bay_id}-${job.train_id}-${job.start.toISOString()}`}
                          className="flex border-b border-white/10 bg-white/[0.015] transition hover:bg-white/[0.06]"
                        >
                          <div
                            className="flex-shrink-0 border-r border-white/10 p-4"
                            style={{ width: `${LEFT_COLUMN_WIDTH_REM}rem` }}
                          >
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-semibold text-white">{bayLabel}</p>
                              {job.priority && job.priority.toLowerCase() !== 'medium' && (
                                <Badge variant={getPriorityVariant(job.priority)} className="text-[11px] uppercase">
                                  {toTitleCase(job.priority)} priority
                                </Badge>
                              )}
                            </div>
                            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-white/70">
                              <Badge variant="secondary" className="text-[11px] uppercase tracking-wide">
                                Train {job.train_id}
                              </Badge>
                              <Badge variant={palette.badgeVariant} className="text-[11px]">
                                {formatJobType(job.jobType)}
                              </Badge>
                              {job.assignedCrew && (
                                <span className="rounded-full border border-white/15 bg-white/10 px-2 py-0.5 text-[11px] text-white/60">
                                  Crew: {job.assignedCrew}
                                </span>
                              )}
                            </div>
                            <dl className="mt-3 grid grid-cols-3 gap-2 text-[11px] text-white/60">
                              <div>
                                <dt className="text-[10px] uppercase tracking-wide text-white/40">Start</dt>
                                <dd className="font-medium text-white/70">{formatTime(job.start)}</dd>
                              </div>
                              <div>
                                <dt className="text-[10px] uppercase tracking-wide text-white/40">End</dt>
                                <dd className="font-medium text-white/70">{formatTime(job.end)}</dd>
                              </div>
                              <div>
                                <dt className="text-[10px] uppercase tracking-wide text-white/40">Duration</dt>
                                <dd className="font-medium text-white/70">{job.durationHours.toFixed(1)} h</dd>
                              </div>
                            </dl>
                          </div>
                          <div
                            className="relative flex-1"
                            style={{ minWidth: `${Math.max(timeSlots.length, SLOTS_PER_WINDOW) * SLOT_WIDTH_REM}rem` }}
                          >
                            <div className="pointer-events-none absolute inset-0 flex">
                              {timeSlots.map((_, idx) => (
                                <div
                                  key={`grid-${job.bay_id}-${job.start.toISOString()}-${idx}`}
                                  className={`h-full border-l border-white/10 ${idx % 2 === 1 ? 'bg-white/[0.05]' : 'bg-transparent'}`}
                                  style={{ width: `${SLOT_WIDTH_REM}rem` }}
                                />
                              ))}
                            </div>
                            <div className="relative h-20">
                              <div
                                className={`absolute top-3 flex h-14 items-center overflow-hidden rounded-2xl border px-4 text-sm font-medium backdrop-blur ${palette.barClass} ${palette.borderClass} ${palette.textClass}`}
                                style={{ left: `${leftRem}rem`, width: `${widthRem}rem` }}
                              >
                                <div className="flex w-full items-center justify-between gap-3">
                                  <span className="truncate">{formatJobType(job.jobType)}</span>
                                  <span className="text-xs text-white/80">{job.durationHours.toFixed(1)} h</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            )}
            {jobTypeLegend.length > 0 && (
              <div className="mt-6 flex flex-wrap gap-4 text-xs text-white/60">
                {jobTypeLegend.map(({ label, palette }) => (
                  <span key={label} className="flex items-center gap-2">
                    <span className={`h-2.5 w-2.5 rounded-full border border-white/40 ${palette.dotClass}`} />
                    <span className="font-medium text-white/70">{label}</span>
                  </span>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
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
  icon: typeof ClipboardList
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
