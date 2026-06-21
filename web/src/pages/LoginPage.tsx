import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthProvider'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'

export function LoginPage() {
  const { user, configured, signInWithGoogle, loading } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (loading) return null
  if (user) return <Navigate to="/" replace />

  const onSignIn = async () => {
    setError(null)
    setBusy(true)
    try {
      await signInWithGoogle()
      navigate('/')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
      <Card className="w-full max-w-sm">
        <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
          <h1 className="text-lg font-semibold">Personal Finance Assistant</h1>
          {configured ? (
            <>
              <p className="text-sm text-slate-500">Sign in to view your finances.</p>
              <Button onClick={onSignIn} disabled={busy} className="w-full">
                {busy ? <Spinner /> : null}
                Continue with Google
              </Button>
              {error && <p className="text-xs text-red-600">{error}</p>}
            </>
          ) : (
            <>
              <p className="text-sm text-slate-500">
                Firebase isn’t configured. Set <code>VITE_FIREBASE_*</code> in
                <code> .env.local</code> to enable Google sign-in, or run the backend with
                <code> AUTH_DISABLED=true</code> for local development.
              </p>
              <Button variant="outline" className="w-full" onClick={() => navigate('/')}>
                Continue in local mode
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
