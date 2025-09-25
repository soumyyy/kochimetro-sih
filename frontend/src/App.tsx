import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './pages/Dashboard'
import PlanBoard from './pages/PlanBoard'
import IBLGantt from './pages/IBLGantt'
import DepotView from './pages/DepotView'
import SponsorDash from './pages/SponsorDash'
import { Toaster } from './components/ui/sonner'
import { PlanDateProvider } from './context/PlanDateContext'
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <PlanDateProvider>
          <div className="app-shell min-h-screen">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/planboard" element={<PlanBoard />} />
              <Route path="/ibl-gantt" element={<IBLGantt />} />
              <Route path="/depot" element={<DepotView />} />
              <Route path="/sponsors" element={<SponsorDash />} />
            </Routes>
            <Toaster />
          </div>
        </PlanDateProvider>
      </Router>
    </QueryClientProvider>
  )
}

export default App
