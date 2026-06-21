import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { AlertsPage } from '@/pages/AlertsPage'
import { BudgetsPage } from '@/pages/BudgetsPage'
import { ConnectionsPage } from '@/pages/ConnectionsPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { LoginPage } from '@/pages/LoginPage'
import { RecurringPage } from '@/pages/RecurringPage'
import { RulesPage } from '@/pages/RulesPage'
import { TransactionsPage } from '@/pages/TransactionsPage'

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/transactions" element={<TransactionsPage />} />
        <Route path="/budgets" element={<BudgetsPage />} />
        <Route path="/recurring" element={<RecurringPage />} />
        <Route path="/rules" element={<RulesPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/connections" element={<ConnectionsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
