import Layout from '../components/Layout'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Users,
  Calendar
} from 'lucide-react'

const stats = [
  {
    name: 'Active Trains',
    value: '8',
    change: '+1 from yesterday',
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

export default function Dashboard() {
  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-600">
            Overview of Kochi Metro train induction and IBL planning
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.name}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  {stat.name}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-gray-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                <p className={`text-xs ${
                  stat.changeType === 'increase' ? 'text-green-600' :
                  stat.changeType === 'warning' ? 'text-yellow-600' :
                  stat.changeType === 'success' ? 'text-green-600' :
                  'text-gray-600'
                }`}>
                  {stat.change}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Today's Plan */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Calendar className="mr-2 h-5 w-5" />
                Today's Plan (2024-09-25)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-green-600">8</div>
                  <div className="text-sm text-gray-600">Active</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-blue-600">6</div>
                  <div className="text-sm text-gray-600">Standby</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-orange-600">11</div>
                  <div className="text-sm text-gray-600">IBL</div>
                </div>
              </div>
              <div className="pt-4 border-t">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Optimization Score</span>
                  <Badge variant="success">95.2%</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* System Alerts */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <AlertTriangle className="mr-2 h-5 w-5" />
                System Alerts
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center space-x-3">
                <Badge variant="warning">Medium</Badge>
                <span className="text-sm text-gray-600">
                  Train TS-13 requires deep cleaning
                </span>
              </div>
              <div className="flex items-center space-x-3">
                <Badge variant="success">Resolved</Badge>
                <span className="text-sm text-gray-600">
                  Bay B-05 maintenance completed
                </span>
              </div>
              <div className="flex items-center space-x-3">
                <Badge variant="info">Info</Badge>
                <span className="text-sm text-gray-600">
                  Weekly mileage balancing applied
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Plans */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="mr-2 h-5 w-5" />
              Recent Plans
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentPlans.map((plan) => (
                <div key={plan.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="text-sm font-medium text-gray-900">
                      {new Date(plan.date).toLocaleDateString()}
                    </div>
                    <Badge variant={plan.status === 'completed' ? 'success' : 'default'}>
                      {plan.status}
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-6 text-sm text-gray-600">
                    <div className="flex items-center">
                      <Activity className="mr-1 h-4 w-4 text-green-500" />
                      {plan.active}
                    </div>
                    <div className="flex items-center">
                      <Users className="mr-1 h-4 w-4 text-blue-500" />
                      {plan.standby}
                    </div>
                    <div className="flex items-center">
                      <Clock className="mr-1 h-4 w-4 text-orange-500" />
                      {plan.ibl}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
