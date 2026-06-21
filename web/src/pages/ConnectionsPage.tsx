import { useState } from 'react'
import { CheckCircle2, RefreshCw, TriangleAlert } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CenteredSpinner, Spinner } from '@/components/ui/spinner'
import { useItems } from '@/hooks/useApi'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import type { ItemStatus } from '@/types'

function StatusBadge({ status }: { status: ItemStatus }) {
  if (status === 'active') {
    return (
      <Badge className="bg-emerald-100 text-emerald-700">
        <CheckCircle2 className="h-3 w-3" /> Connected
      </Badge>
    )
  }
  if (status === 'needsReauth') {
    return (
      <Badge className="bg-orange-100 text-orange-700">
        <TriangleAlert className="h-3 w-3" /> Needs re-auth
      </Badge>
    )
  }
  return (
    <Badge className="bg-red-100 text-red-700">
      <TriangleAlert className="h-3 w-3" /> Error
    </Badge>
  )
}

export function ConnectionsPage() {
  const itemsQ = useItems()
  const [busyId, setBusyId] = useState<string | null>(null)
  const [note, setNote] = useState<string | null>(null)

  const reconnect = async (itemId: string) => {
    setBusyId(itemId)
    setNote(null)
    try {
      await api.reauthLinkToken(itemId)
      // In production this token opens Plaid Link in update mode (react-plaid-link / the mobile
      // app). Here we confirm the token was minted.
      setNote('Re-auth link token created — open Plaid Link (update mode) to finish reconnecting.')
    } catch (e) {
      setNote(`Failed to start re-auth: ${(e as Error).message}`)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">Connections</h1>
      <p className="text-sm text-slate-500">
        Bank connections sync automatically via Plaid webhooks. New banks are added through Plaid
        Link (in the mobile app); broken connections can be repaired here.
      </p>

      {note && (
        <div className="rounded-md bg-slate-100 px-4 py-2 text-sm text-slate-700">{note}</div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Linked institutions</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {itemsQ.isLoading ? (
            <CenteredSpinner label="Loading connections…" />
          ) : (itemsQ.data ?? []).length === 0 ? (
            <p className="p-6 text-sm text-slate-400">
              No banks linked yet. Connect one from the mobile app to start syncing.
            </p>
          ) : (
            <div className="divide-y divide-slate-100">
              {(itemsQ.data ?? []).map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between gap-3 px-5 py-4 text-sm"
                >
                  <div>
                    <div className="font-medium">{item.institution_name || item.id}</div>
                    <div className="text-xs text-slate-400">
                      {item.last_sync_at
                        ? `Last synced ${formatDate(item.last_sync_at)}`
                        : 'Not yet synced'}
                      {item.products.length > 0 && ` · ${item.products.join(', ')}`}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={item.status} />
                    {item.status === 'needsReauth' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => reconnect(item.id)}
                        disabled={busyId === item.id}
                      >
                        {busyId === item.id ? <Spinner /> : <RefreshCw className="h-4 w-4" />}
                        Reconnect
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
