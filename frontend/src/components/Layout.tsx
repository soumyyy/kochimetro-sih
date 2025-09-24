import type { ReactNode } from 'react'
import { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Calendar,
  MapPin,
  BarChart3,
  Menu,
  X,
  Sparkles,
  Clock
} from 'lucide-react'

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

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const planMeta = useMemo(() => {
    return {
      windowLabel: 'Tonight · 21:00 – 05:30 IST',
      lastRefresh: '28 Jan 2025 · 18:45 IST',
      datasetRange: 'Synthetic snapshot · 01 Jan – 28 Jan 2025',
    }
  }, [])

  return (
    <div className="flex min-h-screen bg-slate-50 bg-[radial-gradient(circle_at_20%_20%,rgba(59,130,246,0.1),transparent_55%),radial-gradient(circle_at_80%_0%,rgba(96,165,250,0.08),transparent_45%),linear-gradient(180deg,rgba(15,23,42,0.05)_0%,rgba(15,23,42,0.02)_45%,rgba(15,23,42,0)_100%)]">
      {/* Sidebar for mobile */}
      <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-slate-900/60" onClick={() => setSidebarOpen(false)} />
        <div className="relative flex w-full max-w-xs flex-1 flex-col bg-slate-900 text-slate-100 shadow-2xl">
          <div className="absolute top-0 right-0 -mr-12 pt-4">
            <button
              type="button"
              className="ml-1 flex h-10 w-10 items-center justify-center rounded-full bg-slate-700/60 focus:outline-none focus:ring-2 focus:ring-slate-300"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-5 w-5 text-slate-100" />
            </button>
          </div>
          <div className="flex flex-1 flex-col pt-6 pb-6 overflow-y-auto">
            <div className="px-6">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">KMRL Planner</p>
              <h1 className="mt-2 text-2xl font-semibold text-white">Induction & IBL</h1>
              <p className="mt-1 text-xs text-slate-400">{planMeta.datasetRange}</p>
            </div>
            <nav className="mt-8 flex-1 space-y-1 px-2">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`group flex flex-col rounded-lg px-3 py-3 text-sm transition ${
                      isActive
                        ? 'bg-white/10 text-white shadow-inner'
                        : 'text-slate-300 hover:bg-white/5 hover:text-white'
                    }`}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <div className="flex items-center gap-3">
                      <item.icon className="h-4 w-4" />
                      <span className="font-medium">{item.name}</span>
                    </div>
                    <span className="mt-1 text-[11px] text-slate-400">{item.blurb}</span>
                  </Link>
                )
              })}
            </nav>
          </div>
        </div>
      </div>

      {/* Static sidebar for desktop */}
      <aside className="hidden lg:flex lg:w-72 lg:flex-col">
        <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden bg-slate-900 text-slate-100">
          <div className="absolute inset-0 opacity-60" aria-hidden="true">
            <div className="h-full w-full bg-gradient-to-b from-slate-900 via-slate-900/90 to-slate-950" />
          </div>
          <div className="relative z-10 flex flex-1 flex-col pt-8 pb-6">
            <div className="px-6">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">KMRL Planner</p>
              <h1 className="mt-2 text-2xl font-semibold text-white">Induction & IBL</h1>
              <p className="mt-2 text-xs leading-snug text-slate-400">{planMeta.datasetRange}</p>
            </div>
            <nav className="mt-8 flex-1 space-y-2 px-4">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`group flex flex-col rounded-xl px-4 py-3 transition ${
                      isActive
                        ? 'bg-white/12 text-white shadow-[0_20px_45px_-30px_rgba(15,23,42,0.9)]'
                        : 'text-slate-300 hover:bg-white/6 hover:text-white'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <item.icon className="h-4 w-4" />
                      <span className="text-sm font-medium">{item.name}</span>
                    </div>
                    <span className="mt-1 text-[11px] text-slate-400">{item.blurb}</span>
                  </Link>
                )
              })}
            </nav>
            <div className="px-6 pt-4">
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wider text-slate-400">Plan window</p>
                <p className="mt-1 flex items-center gap-2 text-sm font-medium text-white">
                  <Clock className="h-4 w-4 text-slate-300" />
                  Tonight · 21:00 – 05:30 IST
                </p>
                <p className="mt-1 text-[11px] text-slate-400">Last refresh {planMeta.lastRefresh}</p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col lg:pl-0">
        <header className="sticky top-0 z-40 flex h-16 items-center border-b border-slate-200/60 bg-white/85 backdrop-blur">
          <button
            type="button"
            className="border-r border-slate-200 px-4 text-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-300 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>
          <div className="flex flex-1 items-center justify-between px-4 sm:px-6 lg:px-8">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-primary-600">Plan window</p>
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary-600" />
                <span className="text-sm font-semibold text-slate-800">{planMeta.windowLabel}</span>
              </div>
            </div>
            <div className="hidden items-center gap-3 md:flex">
              <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-100 px-3 py-1">
                <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Last refresh</span>
                <span className="text-xs font-semibold text-slate-700">{planMeta.lastRefresh}</span>
              </div>
              <button className="inline-flex items-center rounded-full border border-slate-200 bg-slate-100/70 px-3.5 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100">
                Dataset notes
              </button>
              <Link
                to="/planboard"
                className="inline-flex items-center rounded-full bg-blue-600 px-3.5 py-1.5 text-sm font-semibold text-white shadow-[0_18px_35px_-20px_rgba(37,99,235,0.75)] transition hover:bg-blue-700"
              >
                Open plan board
              </Link>
            </div>
          </div>
        </header>

        <div className="relative flex-1 overflow-y-auto focus:outline-none">
          <div
            className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(148,163,184,0.12)_1px,transparent_1px),linear-gradient(to_bottom,rgba(148,163,184,0.12)_1px,transparent_1px)] bg-[length:32px_32px] opacity-20"
            aria-hidden="true"
          />
          <main className="relative z-10 py-6">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-10">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
