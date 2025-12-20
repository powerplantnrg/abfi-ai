import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DashboardLayout } from '@/components/dashboard/Layout'
import { SentimentDashboard } from '@/pages/SentimentDashboard'
import { PricesDashboard } from '@/pages/PricesDashboard'
import { PolicyDashboard } from '@/pages/PolicyDashboard'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<SentimentDashboard />} />
            <Route path="prices" element={<PricesDashboard />} />
            <Route path="policy" element={<PolicyDashboard />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
