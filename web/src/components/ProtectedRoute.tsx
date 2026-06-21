import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthProvider'
import { CenteredSpinner } from '@/components/ui/spinner'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading, configured } = useAuth()

  if (loading) return <CenteredSpinner label="Loading…" />
  // When Firebase is configured we require a signed-in user; when it isn't (local dev with the
  // backend running AUTH_DISABLED) we let the app through unauthenticated.
  if (configured && !user) return <Navigate to="/login" replace />
  return <>{children}</>
}
