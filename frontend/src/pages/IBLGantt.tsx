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
}

interface GanttJob {
  bay_id: string
  train_id: string
  start: Date
  end: Date
  durationHours: number
  startIndex: number
  endIndex: number
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

const formatTime = (date: Date): string =>
  date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })

const minutesBetween = (start: Date, end: Date): number =>
  (end.getTime() - start.getTime()) / (1000 * 60)

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
        }
      })
      .sort((a, b) => a.start.getTime() - b.start.getTime())
  }, [planDetails?.ibl_gantt, windowStart])

  const uniqueBays = useMemo(() => new Set(jobs.map((job) => job.bay_id)).size, [jobs])
  const uniqueTrains = useMemo(() => new Set(jobs.map((job) => job.train_id)).size, [jobs])
  const totalHours = useMemo(
    () => jobs.reduce((sum, job) => sum + job.durationHours, 0),
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
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-800">
          {message}
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
          <div className="h-[480px] rounded-2xl bg-slate-100 animate-pulse" />
        </div>
      </Layout>
    )
  }

  if (!planMeta || !planId) {
    return (
      <Layout>
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-600">
          No plans found. Seed the database and refresh to view the IBL schedule.
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">IBL Gantt Chart</h1>
            <p className="mt-1 text-sm text-slate-600">
              Night work schedule for {planDateIso ? new Date(planDateIso).toLocaleDateString() : 'upcoming plan'}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="info">Plan status: {planStatus}</Badge>
            {planDetails?.plan_id && (
              <Badge variant="secondary">Plan ID: {planDetails.plan_id}</Badge>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <SummaryCard
            label="Night jobs"
            value={jobs.length}
            icon={ClipboardList}
            accent="text-blue-600"
          />
          <SummaryCard
            label="Total hours"
            value={totalHours.toFixed(1)}
            icon={Clock}
            accent="text-emerald-600"
          />
          <SummaryCard
            label="Unique trains"
            value={uniqueTrains}
            icon={TrainFront}
            accent="text-indigo-600"
          />
          <SummaryCard
            label="Bays utilised"
            value={uniqueBays}
            icon={MapPin}
            accent="text-amber-600"
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Maintenance schedule</CardTitle>
          </CardHeader>
          <CardContent>
            {jobs.length === 0 || !windowStart ? (
              <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-12 text-center text-sm text-slate-500">
                No IBL occupancy recorded for this plan window.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <div className="min-w-full">
                  <div className="flex border-b">
                    <div className="w-36 flex-shrink-0 p-2 font-semibold text-sm text-slate-900">
                      Bay / Train
                    </div>
                    {timeSlots.map((label) => (
                      <div
                        key={label}
                        className="w-16 flex-shrink-0 border-l p-2 text-center text-xs font-medium text-slate-500"
                      >
                        {label}
                      </div>
                    ))}
                  </div>

                  <div className="space-y-1">
                    {jobs.map((job) => {
                      const widthRem = Math.max(job.endIndex - job.startIndex, 0.5) * SLOT_WIDTH_REM
                      const leftRem = Math.max(job.startIndex, 0) * SLOT_WIDTH_REM

                      return (
                        <div key={`${job.bay_id}-${job.train_id}-${job.start.toISOString()}`} className="flex border-b border-slate-100">
                          <div className="w-36 flex-shrink-0 p-2">
                            <div className="font-medium text-sm text-slate-900">{job.bay_id}</div>
                            <div className="text-xs text-slate-600">{job.train_id}</div>
                            <div className="text-xs text-slate-500">
                              {formatTime(job.start)} – {formatTime(job.end)}
                            </div>
                          </div>
                          <div className="relative flex-1">
                            <div
                              className="absolute top-1 flex h-10 items-center overflow-hidden rounded border border-blue-200 bg-blue-50 px-3 text-xs text-blue-800"
                              style={{ left: `${leftRem}rem`, width: `${widthRem}rem` }}
                            >
                              <span className="truncate">{job.durationHours.toFixed(1)} h scheduled</span>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
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
