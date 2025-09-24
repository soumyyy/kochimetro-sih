import { useState } from 'react'
import Layout from '../components/Layout'
import { Card, CardContent} from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import {
  Activity,
  Users,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Play,
  Settings
} from 'lucide-react'

interface Train {
  id: string
  status: 'active' | 'standby' | 'ibl'
  bay?: string
  priority: 'high' | 'medium' | 'low'
  fitness_ok: boolean
  wo_blocking: boolean
  brand_deficit: number
  mileage_deviation: number
  cleaning_needed: boolean
}

const mockTrains: Train[] = [
  { id: 'TS-01', status: 'active', priority: 'high', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: -500, cleaning_needed: false },
  { id: 'TS-02', status: 'active', priority: 'high', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: 200, cleaning_needed: false },
  { id: 'TS-03', status: 'active', priority: 'medium', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: -200, cleaning_needed: false },
  { id: 'TS-04', status: 'active', priority: 'high', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: 100, cleaning_needed: false },
  { id: 'TS-05', status: 'active', priority: 'medium', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: -300, cleaning_needed: false },
  { id: 'TS-06', status: 'active', priority: 'high', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: 400, cleaning_needed: false },
  { id: 'TS-07', status: 'active', priority: 'high', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: 150, cleaning_needed: false },
  { id: 'TS-08', status: 'active', priority: 'medium', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: -100, cleaning_needed: false },
  { id: 'TS-09', status: 'standby', priority: 'medium', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: 0, cleaning_needed: false },
  { id: 'TS-10', status: 'standby', priority: 'medium', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: 50, cleaning_needed: false },
  { id: 'TS-11', status: 'standby', priority: 'low', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: -50, cleaning_needed: false },
  { id: 'TS-12', status: 'standby', priority: 'medium', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: 25, cleaning_needed: false },
  { id: 'TS-13', status: 'standby', priority: 'low', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: -25, cleaning_needed: false },
  { id: 'TS-14', status: 'standby', priority: 'medium', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: 75, cleaning_needed: false },
  { id: 'TS-15', status: 'ibl', bay: 'B-01', priority: 'high', fitness_ok: false, wo_blocking: true, brand_deficit: 5.2, mileage_deviation: 800, cleaning_needed: true },
  { id: 'TS-16', status: 'ibl', bay: 'B-02', priority: 'medium', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: -400, cleaning_needed: true },
  { id: 'TS-17', status: 'ibl', bay: 'B-03', priority: 'high', fitness_ok: false, wo_blocking: true, brand_deficit: 3.1, mileage_deviation: 600, cleaning_needed: true },
  { id: 'TS-18', status: 'ibl', bay: 'B-04', priority: 'medium', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: -300, cleaning_needed: true },
  { id: 'TS-19', status: 'ibl', bay: 'B-05', priority: 'low', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: -200, cleaning_needed: true },
  { id: 'TS-20', status: 'ibl', bay: 'B-06', priority: 'medium', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: -500, cleaning_needed: true },
  { id: 'TS-21', status: 'ibl', bay: 'B-07', priority: 'high', fitness_ok: false, wo_blocking: true, brand_deficit: 4.5, mileage_deviation: 700, cleaning_needed: true },
  { id: 'TS-22', status: 'ibl', bay: 'B-08', priority: 'medium', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: -350, cleaning_needed: true },
  { id: 'TS-23', status: 'ibl', bay: 'B-09', priority: 'low', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: -150, cleaning_needed: true },
  { id: 'TS-24', status: 'ibl', bay: 'B-10', priority: 'medium', fitness_ok: true, wo_blocking: false, brand_deficit: 0, mileage_deviation: -250, cleaning_needed: true },
  { id: 'TS-25', status: 'ibl', bay: 'B-11', priority: 'high', fitness_ok: false, wo_blocking: true, brand_deficit: 6.1, mileage_deviation: 900, cleaning_needed: true },
]

const statusConfig = {
  active: { color: 'bg-green-100 text-green-800', icon: Activity },
  standby: { color: 'bg-blue-100 text-blue-800', icon: Users },
  ibl: { color: 'bg-orange-100 text-orange-800', icon: Clock },
}

export default function PlanBoard() {
  const [trains] = useState<Train[]>(mockTrains)

  const activeTrains = trains.filter(t => t.status === 'active')
  const standbyTrains = trains.filter(t => t.status === 'standby')
  const iblTrains = trains.filter(t => t.status === 'ibl')

  const TrainCard = ({ train }: { train: Train }) => {
    const StatusIcon = statusConfig[train.status].icon

    return (
      <Card className="glass-panel border-none cursor-pointer transition-shadow hover:shadow-lg">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <h3 className="font-semibold text-gray-900">{train.id}</h3>
              <Badge className={statusConfig[train.status].color}>
                <StatusIcon className="w-3 h-3 mr-1" />
                {train.status.toUpperCase()}
              </Badge>
            </div>
            {train.bay && (
              <Badge variant="secondary">Bay {train.bay}</Badge>
            )}
          </div>

          <div className="space-y-1">
            {/* Status indicators */}
            <div className="flex items-center space-x-2">
              {train.fitness_ok ? (
                <CheckCircle className="w-4 h-4 text-green-500" />
              ) : (
                <XCircle className="w-4 h-4 text-red-500" />
              )}
              <span className="text-xs text-gray-600">Fitness</span>

              {train.wo_blocking ? (
                <AlertTriangle className="w-4 h-4 text-red-500 ml-2" />
              ) : (
                <CheckCircle className="w-4 h-4 text-green-500 ml-2" />
              )}
              <span className="text-xs text-gray-600">WO</span>
            </div>

            {/* Key metrics */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              {train.brand_deficit > 0 && (
                <div className="text-yellow-600">
                  Brand Δ: {train.brand_deficit}h
                </div>
              )}
              <div className={train.mileage_deviation > 0 ? 'text-red-600' : 'text-blue-600'}>
                Mileage: {train.mileage_deviation > 0 ? '+' : ''}{train.mileage_deviation}
              </div>
            </div>

            {train.cleaning_needed && (
              <div className="text-xs text-orange-600">
                🧹 Cleaning needed
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Plan Board</h1>
            <p className="mt-1 text-sm text-gray-600">
              Drag and drop trains between columns to modify assignments
            </p>
          </div>
          <div className="flex space-x-3">
            <button className="btn btn-secondary">
              <Settings className="w-4 h-4 mr-2" />
              Weights
            </button>
            <button className="btn btn-primary">
              <Play className="w-4 h-4 mr-2" />
              Run Optimization
            </button>
          </div>
        </div>

        {/* KPI Summary */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <Card className="glass-panel border-none">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-green-600">{activeTrains.length}</div>
              <div className="text-sm text-gray-600">Active (7-9 required)</div>
            </CardContent>
          </Card>
          <Card className="glass-panel border-none">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-blue-600">{standbyTrains.length}</div>
              <div className="text-sm text-gray-600">Standby reserve</div>
            </CardContent>
          </Card>
          <Card className="glass-panel border-none">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-orange-600">{iblTrains.length}</div>
              <div className="text-sm text-gray-600">In IBL</div>
            </CardContent>
          </Card>
          <Card className="glass-panel border-none">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-gray-600">
                {trains.filter(t => t.fitness_ok).length}/{trains.length}
              </div>
              <div className="text-sm text-gray-600">Fitness OK</div>
            </CardContent>
          </Card>
        </div>

        {/* Plan Board */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Column */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <Activity className="w-5 h-5 mr-2 text-green-500" />
              Active ({activeTrains.length}/9)
            </h2>
            <div className="space-y-3 min-h-[600px]">
              {activeTrains.map((train) => (
                <TrainCard key={train.id} train={train} />
              ))}
            </div>
          </div>

          {/* Standby Column */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <Users className="w-5 h-5 mr-2 text-blue-500" />
              Standby ({standbyTrains.length})
            </h2>
            <div className="space-y-3 min-h-[600px]">
              {standbyTrains.map((train) => (
                <TrainCard key={train.id} train={train} />
              ))}
            </div>
          </div>

          {/* IBL Column */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <Clock className="w-5 h-5 mr-2 text-orange-500" />
              IBL ({iblTrains.length})
            </h2>
            <div className="space-y-3 min-h-[600px]">
              {iblTrains.map((train) => (
                <TrainCard key={train.id} train={train} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
