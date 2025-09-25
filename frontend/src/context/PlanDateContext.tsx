import { createContext, useCallback, useContext, useMemo, type ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

interface PlanListItem {
  plan_id: string
  plan_date: string
  status: string
}

interface PlanDateOption {
  value: string
  label: string
  status: string
}

interface PlanDateContextValue {
  planDate: string | null
  setPlanDate: (next: string | null) => void
  options: PlanDateOption[]
  isLoadingOptions: boolean
  latestPlanDate: string | null
}

const PlanDateContext = createContext<PlanDateContextValue | undefined>(undefined)

const toTitle = (value: string): string =>
  value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ')

const formatPlanLabel = (iso: string, status: string): string => {
  const formatted = new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
  return `${formatted} · ${toTitle(status)}`
}

const fetchPlanList = async (): Promise<PlanListItem[]> => {
  const { data } = await axios.get<{ plans: PlanListItem[] }>(`${API_BASE_URL}/api/v1/plans/list`, {
    params: { limit: 120, offset: 0 },
  })
  return data.plans ?? []
}

export function PlanDateProvider({ children }: { children: ReactNode }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedParam = searchParams.get('plan_date')
  const planDate = selectedParam && selectedParam.trim().length ? selectedParam : null

  const { data: plans, isLoading: isLoadingOptions } = useQuery({
    queryKey: ['plan-date-options'],
    queryFn: fetchPlanList,
    staleTime: 5 * 60 * 1000,
  })

  const latestPlanDate = plans?.[0]?.plan_date ?? null

  const options = useMemo<PlanDateOption[]>(() => {
    if (!plans?.length) return []
    return plans.map((plan) => ({
      value: plan.plan_date,
      status: plan.status,
      label: formatPlanLabel(plan.plan_date, plan.status ?? 'unknown'),
    }))
  }, [plans])

  const handleSetPlanDate = useCallback(
    (next: string | null) => {
      const nextParams = new URLSearchParams(searchParams)
      if (next) {
        nextParams.set('plan_date', next)
      } else {
        nextParams.delete('plan_date')
      }
      setSearchParams(nextParams, { replace: true })
    },
    [searchParams, setSearchParams],
  )

  const contextValue = useMemo<PlanDateContextValue>(
    () => ({
      planDate,
      setPlanDate: handleSetPlanDate,
      options,
      isLoadingOptions,
      latestPlanDate,
    }),
    [planDate, handleSetPlanDate, options, isLoadingOptions, latestPlanDate],
  )

  return <PlanDateContext.Provider value={contextValue}>{children}</PlanDateContext.Provider>
}

export function usePlanDate(): PlanDateContextValue {
  const context = useContext(PlanDateContext)
  if (!context) {
    throw new Error('usePlanDate must be used within a PlanDateProvider')
  }
  return context
}
