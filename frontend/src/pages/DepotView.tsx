import { useState } from 'react'
import Layout from '../components/Layout'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import {
  MapPin,
  Navigation,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react'

interface Bay {
  id: string
  depot_id: string
  position: number
  throat_side: 'A' | 'B'
  has_pit: boolean
  washer_accessible: boolean
  usable_length_m: number
  access_time_min: number
  status: 'occupied' | 'available' | 'maintenance'
  current_train?: string
  next_turnout_rank?: number
}

interface Route {
  id: string
  depot_id: string
  throat_side: 'A' | 'B'
  turnout_speed_kmph: number
  lock_time_sec: number
}

const mockBays: Bay[] = [
  { id: 'B-01', depot_id: 'MUTTOM', position: 1, throat_side: 'A', has_pit: true, washer_accessible: true, usable_length_m: 85, access_time_min: 3, status: 'occupied', current_train: 'TS-15', next_turnout_rank: 15 },
  { id: 'B-02', depot_id: 'MUTTOM', position: 2, throat_side: 'A', has_pit: false, washer_accessible: true, usable_length_m: 85, access_time_min: 2, status: 'occupied', current_train: 'TS-17', next_turnout_rank: 17 },
  { id: 'B-03', depot_id: 'MUTTOM', position: 3, throat_side: 'A', has_pit: true, washer_accessible: false, usable_length_m: 85, access_time_min: 4, status: 'occupied', current_train: 'TS-21', next_turnout_rank: 21 },
  { id: 'B-04', depot_id: 'MUTTOM', position: 4, throat_side: 'A', has_pit: false, washer_accessible: true, usable_length_m: 85, access_time_min: 3, status: 'occupied', current_train: 'TS-16', next_turnout_rank: 16 },
  { id: 'B-05', depot_id: 'MUTTOM', position: 5, throat_side: 'A', has_pit: true, washer_accessible: true, usable_length_m: 85, access_time_min: 2, status: 'occupied', current_train: 'TS-18', next_turnout_rank: 18 },
  { id: 'B-06', depot_id: 'MUTTOM', position: 6, throat_side: 'B', has_pit: false, washer_accessible: false, usable_length_m: 85, access_time_min: 5, status: 'occupied', current_train: 'TS-25', next_turnout_rank: 25 },
  { id: 'B-07', depot_id: 'MUTTOM', position: 7, throat_side: 'B', has_pit: true, washer_accessible: true, usable_length_m: 85, access_time_min: 3, status: 'occupied', current_train: 'TS-19', next_turnout_rank: 19 },
  { id: 'B-08', depot_id: 'MUTTOM', position: 8, throat_side: 'B', has_pit: false, washer_accessible: true, usable_length_m: 85, access_time_min: 4, status: 'occupied', current_train: 'TS-20', next_turnout_rank: 20 },
  { id: 'B-09', depot_id: 'MUTTOM', position: 9, throat_side: 'B', has_pit: true, washer_accessible: false, usable_length_m: 85, access_time_min: 2, status: 'occupied', current_train: 'TS-22', next_turnout_rank: 22 },
  { id: 'B-10', depot_id: 'MUTTOM', position: 10, throat_side: 'B', has_pit: false, washer_accessible: true, usable_length_m: 85, access_time_min: 3, status: 'occupied', current_train: 'TS-23', next_turnout_rank: 23 },
  { id: 'B-11', depot_id: 'MUTTOM', position: 11, throat_side: 'B', has_pit: true, washer_accessible: true, usable_length_m: 85, access_time_min: 4, status: 'occupied', current_train: 'TS-24', next_turnout_rank: 24 },
  { id: 'B-12', depot_id: 'MUTTOM', position: 12, throat_side: 'B', has_pit: false, washer_accessible: false, usable_length_m: 85, access_time_min: 3, status: 'available' },
  { id: 'B-13', depot_id: 'MUTTOM', position: 13, throat_side: 'B', has_pit: true, washer_accessible: true, usable_length_m: 85, access_time_min: 2, status: 'available' },
  { id: 'B-14', depot_id: 'MUTTOM', position: 14, throat_side: 'B', has_pit: false, washer_accessible: true, usable_length_m: 85, access_time_min: 4, status: 'maintenance' },
  { id: 'B-15', depot_id: 'MUTTOM', position: 15, throat_side: 'B', has_pit: true, washer_accessible: false, usable_length_m: 85, access_time_min: 3, status: 'available' },
]

const mockRoutes: Route[] = [
  { id: 'R-A-1', depot_id: 'MUTTOM', throat_side: 'A', turnout_speed_kmph: 15, lock_time_sec: 45 },
  { id: 'R-A-2', depot_id: 'MUTTOM', throat_side: 'A', turnout_speed_kmph: 10, lock_time_sec: 60 },
  { id: 'R-B-1', depot_id: 'MUTTOM', throat_side: 'B', turnout_speed_kmph: 15, lock_time_sec: 45 },
  { id: 'R-B-2', depot_id: 'MUTTOM', throat_side: 'B', turnout_speed_kmph: 10, lock_time_sec: 60 },
]

const getStatusColor = (status: string) => {
  switch (status) {
    case 'occupied': return 'bg-green-100 text-green-800 border-green-300'
    case 'available': return 'bg-gray-100 text-gray-800 border-gray-300'
    case 'maintenance': return 'bg-red-100 text-red-800 border-red-300'
    default: return 'bg-gray-100 text-gray-800 border-gray-300'
  }
}

const getThroatSideColor = (side: string) => {
  return side === 'A' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
}

export default function DepotView() {
  const [bays, setBays] = useState<Bay[]>(mockBays)
  const [routes] = useState<Route[]>(mockRoutes)

  const occupiedBays = bays.filter(b => b.status === 'occupied')
  const availableBays = bays.filter(b => b.status === 'available')
  const maintenanceBays = bays.filter(b => b.status === 'maintenance')

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Depot View</h1>
            <p className="mt-1 text-sm text-gray-600">
              Muttom Depot stabling and turnout planning
            </p>
          </div>
          <div className="flex space-x-3">
            <Badge variant="info">Turnout starts: 05:30</Badge>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <MapPin className="w-8 h-8 text-green-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">{occupiedBays.length}</div>
                  <div className="text-sm text-gray-600">Occupied Bays</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <CheckCircle className="w-8 h-8 text-blue-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">{availableBays.length}</div>
                  <div className="text-sm text-gray-600">Available Bays</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <AlertTriangle className="w-8 h-8 text-red-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">{maintenanceBays.length}</div>
                  <div className="text-sm text-gray-600">Under Maintenance</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <Navigation className="w-8 h-8 text-purple-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">{routes.length}</div>
                  <div className="text-sm text-gray-600">Turnout Routes</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Depot Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bay Status */}
          <Card>
            <CardHeader>
              <CardTitle>Bay Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {bays.map((bay) => (
                  <div
                    key={bay.id}
                    className={`flex items-center justify-between p-3 rounded-lg border ${getStatusColor(bay.status)}`}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="font-medium text-sm">{bay.id}</div>
                      <Badge className={getThroatSideColor(bay.throat_side)}>
                        Side {bay.throat_side}
                      </Badge>
                      {bay.has_pit && (
                        <Badge variant="secondary">Pit</Badge>
                      )}
                      {bay.washer_accessible && (
                        <Badge variant="info">Washer</Badge>
                      )}
                    </div>
                    <div className="text-right">
                      {bay.current_train ? (
                        <div className="text-sm font-medium">{bay.current_train}</div>
                      ) : (
                        <div className="text-sm text-gray-500">Available</div>
                      )}
                      {bay.next_turnout_rank && (
                        <div className="text-xs text-gray-500">
                          Turnout #{bay.next_turnout_rank}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Turnout Schedule */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Navigation className="w-5 h-5 mr-2" />
                Turnout Schedule
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-sm text-gray-600 mb-4">
                  Active trains will depart in the following order:
                </div>

                {occupiedBays
                  .filter(bay => bay.next_turnout_rank)
                  .sort((a, b) => (a.next_turnout_rank || 0) - (b.next_turnout_rank || 0))
                  .map((bay, index) => (
                  <div key={bay.id} className="flex items-center space-x-4 p-3 bg-gray-50 rounded-lg">
                    <div className="flex-shrink-0 w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-medium text-sm">
                      {bay.next_turnout_rank}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-sm text-gray-900">
                        {bay.current_train} from {bay.id}
                      </div>
                      <div className="text-xs text-gray-600">
                        Side {bay.throat_side} • Access: {bay.access_time_min}min
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge variant="info">Scheduled</Badge>
                    </div>
                  </div>
                ))}

                {occupiedBays.filter(bay => bay.next_turnout_rank).length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <Clock className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <div className="text-sm">No turnout schedule available</div>
                    <div className="text-xs">Turnout planning will be available after optimization</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Routes Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Depot Routes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {routes.map((route) => (
                <div key={route.id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium text-sm text-gray-900">{route.id}</div>
                    <Badge className={getThroatSideColor(route.throat_side)}>
                      Side {route.throat_side}
                    </Badge>
                  </div>
                  <div className="space-y-1 text-xs text-gray-600">
                    <div>Speed: {route.turnout_speed_kmph} km/h</div>
                    <div>Lock time: {route.lock_time_sec}s</div>
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
