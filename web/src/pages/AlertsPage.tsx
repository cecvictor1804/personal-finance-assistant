import { AlertTriangle, Bell, Info, ShieldAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { CenteredSpinner } from '@/components/ui/spinner'
import { useAlerts, useMarkAlertRead } from '@/hooks/useApi'
import { cn } from '@/lib/utils'
import { formatDate } from '@/lib/utils'
import type { Severity } from '@/types'

function SeverityIcon({ severity }: { severity: Severity }) {
  if (severity === 'critical') return <ShieldAlert className="h-5 w-5 text-red-600" />
  if (severity === 'warning') return <AlertTriangle className="h-5 w-5 text-amber-500" />
  return <Info className="h-5 w-5 text-slate-400" />
}

export function AlertsPage() {
  const alertsQ = useAlerts()
  const markRead = useMarkAlertRead()
  const alerts = alertsQ.data ?? []
  const unread = alerts.filter((a) => !a.read)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-xl font-semibold">
          <Bell className="h-5 w-5" /> Alerts
        </h1>
        {unread.length > 0 && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => unread.forEach((a) => markRead.mutate(a.id))}
          >
            Mark all read ({unread.length})
          </Button>
        )}
      </div>

      <Card>
        <CardContent className="p-0">
          {alertsQ.isLoading ? (
            <CenteredSpinner label="Loading alerts…" />
          ) : alerts.length === 0 ? (
            <p className="p-6 text-sm text-slate-400">No alerts yet. You’re all clear.</p>
          ) : (
            <div className="divide-y divide-slate-100">
              {alerts.map((a) => (
                <div
                  key={a.id}
                  className={cn(
                    'flex items-start gap-3 px-5 py-3',
                    !a.read && 'bg-slate-50',
                  )}
                >
                  <SeverityIcon severity={a.severity} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{a.title}</span>
                      {!a.read && <span className="h-2 w-2 rounded-full bg-sky-500" />}
                    </div>
                    <p className="text-sm text-slate-600">{a.message}</p>
                    <p className="text-xs text-slate-400">{formatDate(a.created_at)}</p>
                  </div>
                  {!a.read && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => markRead.mutate(a.id)}
                      disabled={markRead.isPending}
                    >
                      Mark read
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
