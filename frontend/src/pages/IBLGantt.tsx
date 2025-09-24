import { useState } from 'react'
import Layout from '../components/Layout'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import {
  Clock,
  Users,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'

interface IBLJob {
  id: string
  train_id: string
  bay_id: string
  start_time: string
  end_time: string
  duration_hours: number
  type: 'cleaning' | 'maintenance' | 'inspection'
  priority: 'high' | 'medium' | 'low'
  assigned_crew: string[]
  status: 'scheduled' | 'in_progress' | 'completed' | 'delayed'
}

const mockJobs: IBLJob[] = [
  {
    id: 'job-001',
    train_id: 'TS-15',
    bay_id: 'B-01',
    start_time: '21:00',
    end_time: '23:30',
    duration_hours: 2.5,
    type: 'cleaning',
    priority: 'high',
    assigned_crew: ['Crew-A', 'Crew-B'],
    status: 'scheduled'
  },
  {
    id: 'job-002',
    train_id: 'TS-17',
    bay_id: 'B-02',
    start_time: '21:15',
    end_time: '22:45',
    duration_hours: 1.5,
    type: 'maintenance',
    priority: 'high',
    assigned_crew: ['Crew-C'],
    status: 'in_progress'
  },
  {
    id: 'job-003',
    train_id: 'TS-21',
    bay_id: 'B-03',
    start_time: '22:00',
    end_time: '01:30',
    duration_hours: 3.5,
    type: 'inspection',
    priority: 'high',
    assigned_crew: ['Crew-D', 'Crew-E'],
    status: 'scheduled'
  },
  {
    id: 'job-004',
    train_id: 'TS-16',
    bay_id: 'B-04',
    start_time: '22:30',
    end_time: '23:15',
    duration_hours: 0.75,
    type: 'cleaning',
    priority: 'medium',
    assigned_crew: ['Crew-F'],
    status: 'scheduled'
  },
  {
    id: 'job-005',
    train_id: 'TS-18',
    bay_id: 'B-05',
    start_time: '23:00',
    end_time: '00:30',
    duration_hours: 1.5,
    type: 'maintenance',
    priority: 'medium',
    assigned_crew: ['Crew-G'],
    status: 'scheduled'
  },
  {
    id: 'job-006',
    train_id: 'TS-25',
    bay_id: 'B-06',
    start_time: '23:30',
    end_time: '02:00',
    duration_hours: 2.5,
    type: 'cleaning',
    priority: 'high',
    assigned_crew: ['Crew-A', 'Crew-B'],
    status: 'delayed'
  },
  {
    id: 'job-007',
    train_id: 'TS-19',
    bay_id: 'B-07',
    start_time: '00:00',
    end_time: '01:00',
    duration_hours: 1.0,
    type: 'cleaning',
    priority: 'low',
    assigned_crew: ['Crew-H'],
    status: 'scheduled'
  },
  {
    id: 'job-008',
    train_id: 'TS-20',
    bay_id: 'B-08',
    start_time: '01:30',
    end_time: '02:30',
    duration_hours: 1.0,
    type: 'maintenance',
    priority: 'medium',
    assigned_crew: ['Crew-I'],
    status: 'scheduled'
  },
  {
    id: 'job-009',
    train_id: 'TS-22',
    bay_id: 'B-09',
    start_time: '02:00',
    end_time: '03:30',
    duration_hours: 1.5,
    type: 'cleaning',
    priority: 'medium',
    assigned_crew: ['Crew-J'],
    status: 'scheduled'
  },
  {
    id: 'job-010',
    train_id: 'TS-23',
    bay_id: 'B-10',
    start_time: '03:00',
    end_time: '04:00',
    duration_hours: 1.0,
    type: 'inspection',
    priority: 'low',
    assigned_crew: ['Crew-K'],
    status: 'scheduled'
  },
  {
    id: 'job-011',
    train_id: 'TS-24',
    bay_id: 'B-11',
    start_time: '04:00',
    end_time: '05:00',
    duration_hours: 1.0,
    type: 'cleaning',
    priority: 'medium',
    assigned_crew: ['Crew-L'],
    status: 'scheduled'
  },
]

const timeSlots = [
  '21:00', '21:30', '22:00', '22:30', '23:00', '23:30',
  '00:00', '00:30', '01:00', '01:30', '02:00', '02:30',
  '03:00', '03:30', '04:00', '04:30', '05:00', '05:30'
]

const getJobPosition = (startTime: string, endTime: string) => {
  const startIndex = timeSlots.indexOf(startTime)
  const endIndex = timeSlots.indexOf(endTime)
  return { startIndex, endIndex }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'bg-green-100 border-green-300'
    case 'in_progress': return 'bg-blue-100 border-blue-300'
    case 'delayed': return 'bg-red-100 border-red-300'
    default: return 'bg-orange-100 border-orange-300'
  }
}

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'high': return 'bg-red-100 text-red-800'
    case 'medium': return 'bg-yellow-100 text-yellow-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

export default function IBLGantt() {
  const [jobs] = useState<IBLJob[]>(mockJobs)

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">IBL Gantt Chart</h1>
            <p className="mt-1 text-sm text-gray-600">
              Night work schedule (21:00 - 05:30)
            </p>
          </div>
          <div className="flex space-x-3">
            <Badge variant="info">Target: 05:30 completion</Badge>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <Clock className="w-8 h-8 text-orange-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">{jobs.length}</div>
                  <div className="text-sm text-gray-600">Total Jobs</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <CheckCircle className="w-8 h-8 text-green-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {jobs.filter(j => j.status === 'completed').length}
                  </div>
                  <div className="text-sm text-gray-600">Completed</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <AlertTriangle className="w-8 h-8 text-red-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {jobs.filter(j => j.status === 'delayed').length}
                  </div>
                  <div className="text-sm text-gray-600">Delayed</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center">
                <Users className="w-8 h-8 text-blue-500 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {jobs.filter(j => j.status === 'in_progress').length}
                  </div>
                  <div className="text-sm text-gray-600">In Progress</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Gantt Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Maintenance Schedule</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <div className="min-w-full">
                {/* Header with time slots */}
                <div className="flex border-b">
                  <div className="w-32 flex-shrink-0 p-2 font-semibold text-sm text-gray-900">
                    Bay / Train
                  </div>
                  {timeSlots.map((time) => (
                    <div
                      key={time}
                      className="w-16 flex-shrink-0 p-2 text-center text-xs font-medium text-gray-500 border-l"
                    >
                      {time}
                    </div>
                  ))}
                </div>

                {/* Job rows */}
                <div className="space-y-1">
                  {jobs.map((job) => {
                    const { startIndex, endIndex } = getJobPosition(job.start_time, job.end_time)
                    const width = (endIndex - startIndex + 1) * 4 // 4rem per slot

                    return (
                      <div key={job.id} className="flex items-center border-b border-gray-100">
                        {/* Job info */}
                        <div className="w-32 flex-shrink-0 p-2">
                          <div className="font-medium text-sm text-gray-900">
                            {job.bay_id}
                          </div>
                          <div className="text-xs text-gray-600">
                            {job.train_id}
                          </div>
                          <Badge className={getPriorityColor(job.priority)}>
                            {job.priority}
                          </Badge>
                        </div>

                        {/* Timeline */}
                        <div className="flex-1 relative h-12">
                          {/* Job bar */}
                          <div
                            className={`absolute top-1 h-10 rounded ${getStatusColor(job.status)} border flex items-center px-2`}
                            style={{
                              left: `${startIndex * 4}rem`,
                              width: `${width}rem`
                            }}
                          >
                            <div className="flex-1 min-w-0">
                              <div className="text-xs font-medium text-gray-900 truncate">
                                {job.type} ({job.duration_hours}h)
                              </div>
                              <div className="text-xs text-gray-600 truncate">
                                {job.assigned_crew.join(', ')}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Empty rows for unoccupied bays */}
                {['B-12', 'B-13', 'B-14', 'B-15'].map((bayId) => (
                  <div key={bayId} className="flex items-center border-b border-gray-100">
                    <div className="w-32 flex-shrink-0 p-2">
                      <div className="font-medium text-sm text-gray-400">
                        {bayId}
                      </div>
                      <div className="text-xs text-gray-300">
                        Available
                      </div>
                    </div>
                    <div className="flex-1 h-12 bg-gray-50"></div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
