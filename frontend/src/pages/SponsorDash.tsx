import { useState } from 'react'
import Layout from '../components/Layout'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  DollarSign
} from 'lucide-react'

interface Sponsor {
  id: string
  name: string
  active_campaigns: number
  total_promised_hours: number
  total_delivered_hours: number
  deficit_hours: number
  over_delivery_hours: number
  penalty_risk: 'low' | 'medium' | 'high'
}

interface Campaign {
  id: string
  sponsor_id: string
  name: string
  promised_hours_per_day: number
  rolling_window_days: number
  penalty_weight: number
  active_trains: string[]
  current_deficit: number
  projected_deficit: number
  status: 'on_track' | 'at_risk' | 'behind_schedule'
}

const mockSponsors: Sponsor[] = [
  {
    id: 'sponsor-001',
    name: 'TechCorp India',
    active_campaigns: 3,
    total_promised_hours: 4800,
    total_delivered_hours: 4650,
    deficit_hours: 150,
    over_delivery_hours: 0,
    penalty_risk: 'medium'
  },
  {
    id: 'sponsor-002',
    name: 'Green Energy Ltd',
    active_campaigns: 2,
    total_promised_hours: 3200,
    total_delivered_hours: 3150,
    deficit_hours: 50,
    over_delivery_hours: 0,
    penalty_risk: 'low'
  },
  {
    id: 'sponsor-003',
    name: 'MetroBank',
    active_campaigns: 4,
    total_promised_hours: 6400,
    total_delivered_hours: 6600,
    deficit_hours: 0,
    over_delivery_hours: 200,
    penalty_risk: 'low'
  },
  {
    id: 'sponsor-004',
    name: 'EduTech Solutions',
    active_campaigns: 1,
    total_promised_hours: 1600,
    total_delivered_hours: 1400,
    deficit_hours: 200,
    over_delivery_hours: 0,
    penalty_risk: 'high'
  },
  {
    id: 'sponsor-005',
    name: 'HealthPlus Pharma',
    active_campaigns: 2,
    total_promised_hours: 3200,
    total_delivered_hours: 3100,
    deficit_hours: 100,
    over_delivery_hours: 0,
    penalty_risk: 'medium'
  },
]

const mockCampaigns: Campaign[] = [
  {
    id: 'camp-001',
    sponsor_id: 'sponsor-001',
    name: 'Tech Innovation 2024',
    promised_hours_per_day: 20,
    rolling_window_days: 30,
    penalty_weight: 1.5,
    active_trains: ['TS-01', 'TS-02', 'TS-03'],
    current_deficit: 45,
    projected_deficit: 120,
    status: 'at_risk'
  },
  {
    id: 'camp-002',
    sponsor_id: 'sponsor-001',
    name: 'Digital Transformation',
    promised_hours_per_day: 15,
    rolling_window_days: 30,
    penalty_weight: 1.2,
    active_trains: ['TS-04', 'TS-05'],
    current_deficit: 30,
    projected_deficit: 75,
    status: 'at_risk'
  },
  {
    id: 'camp-003',
    sponsor_id: 'sponsor-001',
    name: 'AI Solutions Showcase',
    promised_hours_per_day: 25,
    rolling_window_days: 30,
    penalty_weight: 1.8,
    active_trains: ['TS-06', 'TS-07', 'TS-08'],
    current_deficit: 75,
    projected_deficit: 195,
    status: 'behind_schedule'
  },
  {
    id: 'camp-004',
    sponsor_id: 'sponsor-004',
    name: 'Education for All',
    promised_hours_per_day: 40,
    rolling_window_days: 30,
    penalty_weight: 2.0,
    active_trains: ['TS-09', 'TS-10'],
    current_deficit: 200,
    projected_deficit: 520,
    status: 'behind_schedule'
  },
]

const getRiskColor = (risk: string) => {
  switch (risk) {
    case 'high': return 'bg-red-100 text-red-800'
    case 'medium': return 'bg-yellow-100 text-yellow-800'
    case 'low': return 'bg-green-100 text-green-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'on_track': return 'bg-green-100 text-green-800'
    case 'at_risk': return 'bg-yellow-100 text-yellow-800'
    case 'behind_schedule': return 'bg-red-100 text-red-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

export default function SponsorDash() {
  const [sponsors] = useState<Sponsor[]>(mockSponsors)
  const [campaigns] = useState<Campaign[]>(mockCampaigns)

  const totalDeficit = sponsors.reduce((sum, s) => sum + s.deficit_hours, 0)
  const totalOverDelivery = sponsors.reduce((sum, s) => sum + s.over_delivery_hours, 0)
  const highRiskSponsors = sponsors.filter(s => s.penalty_risk === 'high')

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Sponsor Dashboard</h1>
            <p className="mt-1 text-sm text-gray-600">
              Branding exposure and contract compliance
            </p>
          </div>
          <div className="flex space-x-3">
            <Badge variant={totalDeficit > 0 ? 'warning' : 'success'}>
              {totalDeficit > 0 ? `${totalDeficit}h deficit` : 'All targets met'}
            </Badge>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <BarChart3 className="w-8 h-8 text-blue-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">{sponsors.length}</div>
                  <div className="text-sm text-gray-600">Active Sponsors</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <TrendingDown className="w-8 h-8 text-red-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">{totalDeficit}</div>
                  <div className="text-sm text-gray-600">Total Deficit (hrs)</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <TrendingUp className="w-8 h-8 text-green-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">{totalOverDelivery}</div>
                  <div className="text-sm text-gray-600">Over Delivery (hrs)</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <AlertTriangle className="w-8 h-8 text-orange-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">{highRiskSponsors.length}</div>
                  <div className="text-sm text-gray-600">High Risk Sponsors</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sponsor Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Sponsor Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {sponsors.map((sponsor) => {
                const deliveryRate = (sponsor.total_delivered_hours / sponsor.total_promised_hours) * 100

                return (
                  <div key={sponsor.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <h3 className="font-medium text-gray-900">{sponsor.name}</h3>
                        <Badge className={getRiskColor(sponsor.penalty_risk)}>
                          {sponsor.penalty_risk} risk
                        </Badge>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">
                          {deliveryRate.toFixed(1)}% delivered
                        </div>
                        <div className="text-xs text-gray-600">
                          {sponsor.active_campaigns} active campaigns
                        </div>
                      </div>
                    </div>

                    {/* Progress bar */}
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <div
                        className={`h-2 rounded-full ${
                          deliveryRate >= 100 ? 'bg-green-500' :
                          deliveryRate >= 90 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(deliveryRate, 100)}%` }}
                      />
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <div className="text-gray-600">Promised</div>
                        <div className="font-medium">{sponsor.total_promised_hours.toLocaleString()}h</div>
                      </div>
                      <div>
                        <div className="text-gray-600">Delivered</div>
                        <div className="font-medium text-green-600">{sponsor.total_delivered_hours.toLocaleString()}h</div>
                      </div>
                      <div>
                        <div className="text-gray-600">Deficit</div>
                        <div className="font-medium text-red-600">{sponsor.deficit_hours}h</div>
                      </div>
                      <div>
                        <div className="text-gray-600">Over</div>
                        <div className="font-medium text-blue-600">+{sponsor.over_delivery_hours}h</div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Campaign Details */}
        <Card>
          <CardHeader>
            <CardTitle>Campaign Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {campaigns.map((campaign) => {
                const sponsor = sponsors.find(s => s.id === campaign.sponsor_id)
                const deficitRate = (campaign.current_deficit / (campaign.promised_hours_per_day * campaign.rolling_window_days)) * 100

                return (
                  <div key={campaign.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h4 className="font-medium text-gray-900">{campaign.name}</h4>
                        <div className="text-sm text-gray-600">{sponsor?.name}</div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge className={getStatusColor(campaign.status)}>
                          {campaign.status.replace('_', ' ')}
                        </Badge>
                        <Badge variant="secondary">
                          {campaign.active_trains.length} trains
                        </Badge>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <div className="text-gray-600">Daily Target</div>
                        <div className="font-medium">{campaign.promised_hours_per_day}h</div>
                      </div>
                      <div>
                        <div className="text-gray-600">Current Deficit</div>
                        <div className="font-medium text-red-600">{campaign.current_deficit}h</div>
                      </div>
                      <div>
                        <div className="text-gray-600">Projected Deficit</div>
                        <div className="font-medium text-orange-600">{campaign.projected_deficit}h</div>
                      </div>
                      <div>
                        <div className="text-gray-600">Penalty Weight</div>
                        <div className="font-medium">{campaign.penalty_weight}x</div>
                      </div>
                    </div>

                    {/* Deficit visualization */}
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                        <span>Deficit Rate</span>
                        <span>{deficitRate.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1">
                        <div
                          className={`h-1 rounded-full ${
                            deficitRate > 10 ? 'bg-red-500' :
                            deficitRate > 5 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${Math.min(deficitRate, 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
