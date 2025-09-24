import Layout from '../components/Layout'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Link } from 'react-router-dom'
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
  Target
} from 'lucide-react'

const stats = [
  {
    name: 'Active Trains',
    value: '8',
    change: '+1 vs target',
    changeType: 'increase' as const,
    icon: Activity,
  },
  {
    name: 'Standby Trains',
    value: '6',
    change: 'Normal reserve',
    changeType: 'neutral' as const,
    icon: Users,
  },
  {
    name: 'IBL Jobs',
    value: '11',
    change: '3 critical',
    changeType: 'warning' as const,
    icon: Clock,
  },
  {
    name: 'System Status',
    value: 'Healthy',
    change: 'All systems operational',
    changeType: 'success' as const,
    icon: CheckCircle,
  },
]

const recentPlans = [
  {
    id: 'plan-001',
    date: '2024-09-25',
    status: 'completed',
    active: 8,
    standby: 6,
    ibl: 11,
  },
  {
    id: 'plan-002',
    date: '2024-09-24',
    status: 'completed',
    active: 7,
    standby: 7,
    ibl: 11,
  },
  {
    id: 'plan-003',
    date: '2024-09-23',
    status: 'completed',
    active: 9,
    standby: 5,
    ibl: 11,
  },
]

const focusAreas = [
  {
    title: 'Branding recovery',
    description: '4 trains carry >2h deficit – prioritise high-visibility routes tomorrow.',
    icon: Target,
  },
  {
    title: 'Maintenance pressure',
    description: '7 IBL slots booked; 3 trains with critical job cards still pending.',
    icon: ClipboardList,
  },
  {
    title: 'Mileage balancing',
    description: 'Fleet variance within ±320 km after tonight’s plan – monitor standby swaps.',
    icon: TrendingUp,
  },
]

const dataCoverage = [
  { label: 'Synthetic days', value: '28', footnote: '01 Jan – 28 Jan 2025' },
  { label: 'Trains simulated', value: '25', footnote: 'Roster T01 – T25' },
  { label: 'Alerts generated', value: '62', footnote: 'Fitness & maintenance triggers' },
]

export default function Dashboard() {
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
                  Monitor active capacity, IBL pressure, and sponsorship exposure with the
                  generated multi-week dataset. Use the quick links to adjust assignments or
                  inspect the overnight cleaning window.
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
                  <p className="mt-1 font-semibold text-slate-800">25 Sept 2024 (Demo)</p>
                </div>
                <div>
                  <p className="uppercase tracking-[0.18em] text-[11px] text-slate-500">Dataset range</p>
                  <p className="mt-1 font-semibold text-slate-800">01 Jan – 28 Jan 2025</p>
                </div>
                <div>
                  <p className="uppercase tracking-[0.18em] text-[11px] text-slate-500">Plan window</p>
                  <p className="mt-1 font-semibold text-slate-800">21:00 – 05:30 IST</p>
                </div>
                <div>
                  <p className="uppercase tracking-[0.18em] text-[11px] text-slate-500">Last refresh</p>
                  <p className="mt-1 font-semibold text-slate-800">28 Jan 2025 · 18:45 IST</p>
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
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-50 text-primary-600">
                  <stat.icon className="h-4 w-4" />
                </div>
              </CardHeader>
              <CardContent className="space-y-2 p-6 pt-0">
                <div className="text-3xl font-semibold text-slate-900">{stat.value}</div>
                <p className={`text-xs font-medium ${
                  stat.changeType === 'increase'
                    ? 'text-success-600'
                    : stat.changeType === 'warning'
                    ? 'text-warning-600'
                    : stat.changeType === 'success'
                    ? 'text-success-600'
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
                <Calendar className="h-5 w-5 text-primary-600" />
                Tonight&apos;s plan snapshot
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-semibold text-success-600">8</div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Active</div>
                </div>
                <div>
                  <div className="text-2xl font-semibold text-primary-600">6</div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Standby</div>
                </div>
                <div>
                  <div className="text-2xl font-semibold text-warning-600">11</div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">IBL jobs</div>
                </div>
              </div>
              <div className="rounded-xl border border-slate-200/70 bg-slate-50 p-4 text-sm text-slate-600">
                <div className="flex items-center justify-between">
                  <span>Optimiser score</span>
                  <Badge variant="success">95.2%</Badge>
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  Score blends reliability, branding, mileage, and shunting penalties.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-2xl border border-slate-200/60 bg-white/90 shadow-sm backdrop-blur">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-slate-800">
                <AlertTriangle className="h-5 w-5 text-warning-600" />
                System alerts
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-start gap-3 rounded-xl border border-yellow-200/60 bg-yellow-50 p-3 text-sm text-yellow-800">
                <Badge variant="warning">Maintenance</Badge>
                <span>TS-13 booked for deep cleaning – ensure bay turnaround before 02:30.</span>
              </div>
              <div className="flex items-start gap-3 rounded-xl border border-blue-200/60 bg-blue-50 p-3 text-sm text-blue-800">
                <Badge variant="info">Mileage</Badge>
                <span>TS-04 exceeded average mileage by 320 km; rotate to standby tomorrow.</span>
              </div>
              <div className="flex items-start gap-3 rounded-xl border border-green-200/60 bg-green-50 p-3 text-sm text-green-800">
                <Badge variant="success">Resolved</Badge>
                <span>Bay B-05 reopened after traction inspection.</span>
              </div>
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
                  <focus.icon className="h-4 w-4 text-primary-600" />
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
                <TrendingUp className="h-5 w-5 text-primary-600" />
                Recent plans
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {recentPlans.map((plan) => (
                <div key={plan.id} className="flex items-center justify-between rounded-2xl border border-slate-200/60 bg-white/70 p-4 text-sm">
                  <div className="flex items-center gap-4">
                    <div className="font-medium text-slate-800">
                      {new Date(plan.date).toLocaleDateString()}
                    </div>
                    <Badge variant={plan.status === 'completed' ? 'success' : 'default'}>
                      {plan.status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-5 text-slate-500">
                    <div className="flex items-center gap-1">
                      <Activity className="h-4 w-4 text-success-600" />
                      {plan.active}
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="h-4 w-4 text-primary-600" />
                      {plan.standby}
                    </div>
                    <div className="flex items-center">
                      <Clock className="mr-1 h-4 w-4 text-orange-500" />
                      {plan.ibl}
                    </div>
                  </div>
                </div>
              ))}
          </CardContent>
        </Card>
      </div>

        <Card className="rounded-2xl border border-slate-200/60 bg-white/90 shadow-sm backdrop-blur">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg text-slate-800">
              <Sparkles className="h-5 w-5 text-primary-600" />
              Dataset coverage
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {dataCoverage.map((item) => (
              <div key={item.label} className="rounded-2xl border border-slate-200/70 bg-white/70 p-4 text-center">
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
