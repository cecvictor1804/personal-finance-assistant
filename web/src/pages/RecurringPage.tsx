import { useState } from 'react'
import { ArrowDownLeft, ArrowUpRight, RefreshCw } from 'lucide-react'
import { CategoryBadge } from '@/components/CategoryBadge'
import { MoneyText } from '@/components/MoneyText'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CenteredSpinner, Spinner } from '@/components/ui/spinner'
import { useForecast, useRecurring, useRefreshRecurring } from '@/hooks/useApi'
import { cn, formatDate } from '@/lib/utils'
import type { RecurringStream } from '@/types'

const FREQUENCY_LABELS: Record<string, string> = {
  WEEKLY: 'Weekly',
  BIWEEKLY: 'Every 2 weeks',
  SEMI_MONTHLY: 'Twice a month',
  MONTHLY: 'Monthly',
  ANNUALLY: 'Yearly',
  UNKNOWN: 'Irregular',
}

function frequencyLabel(freq: string): string {
  return FREQUENCY_LABELS[freq] ?? freq
}

function StreamRow({ s }: { s: RecurringStream }) {
  return (
    <div className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="truncate font-medium">{s.merchant || s.description || '—'}</span>
          {!s.is_active && (
            <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500">
              inactive
            </span>
          )}
        </div>
        <div className="text-xs text-slate-400">
          {frequencyLabel(s.frequency)}
          {s.last_date ? ` · last ${formatDate(s.last_date)}` : ''}
        </div>
      </div>
      <div className="flex items-center gap-3">
        <CategoryBadge category={s.category} />
        <MoneyText cents={s.average_amount_cents} colorize className="w-24 text-right" />
      </div>
    </div>
  )
}

function StatTile({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-100 p-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-lg font-semibold">{children}</div>
    </div>
  )
}

export function RecurringPage() {
  const [horizon, setHorizon] = useState(30)
  const recurringQ = useRecurring()
  const forecastQ = useForecast(horizon)
  const refresh = useRefreshRecurring()

  const streams = recurringQ.data ?? []
  const outflows = streams.filter((s) => s.flow === 'outflow')
  const inflows = streams.filter((s) => s.flow === 'inflow')

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Recurring & forecast</h1>
        <Button
          size="sm"
          variant="outline"
          onClick={() => refresh.mutate()}
          disabled={refresh.isPending}
        >
          {refresh.isPending ? <Spinner /> : <RefreshCw className="h-4 w-4" />}
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>Cash-flow forecast</CardTitle>
          <div className="flex gap-1">
            {[30, 60].map((h) => (
              <Button
                key={h}
                size="sm"
                variant={horizon === h ? 'default' : 'outline'}
                onClick={() => setHorizon(h)}
              >
                {h}d
              </Button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {forecastQ.isLoading || !forecastQ.data ? (
            <CenteredSpinner label="Projecting…" />
          ) : (
            <>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <StatTile label="Balance now">
                  <MoneyText cents={forecastQ.data.current_balance_cents} />
                </StatTile>
                <StatTile label={`Inflow (${horizon}d)`}>
                  <MoneyText cents={forecastQ.data.projected_inflow_cents} colorize />
                </StatTile>
                <StatTile label={`Outflow (${horizon}d)`}>
                  <MoneyText cents={forecastQ.data.projected_outflow_cents} colorize />
                </StatTile>
                <StatTile label="Projected balance">
                  <MoneyText cents={forecastQ.data.projected_end_balance_cents} colorize />
                </StatTile>
              </div>

              <div className="mt-4">
                <div className="mb-1 text-xs font-medium text-slate-500">Upcoming</div>
                {forecastQ.data.upcoming.length === 0 ? (
                  <p className="text-sm text-slate-400">
                    No upcoming recurring items in this window.
                  </p>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {forecastQ.data.upcoming.slice(0, 12).map((u, i) => (
                      <div key={i} className="flex items-center justify-between py-1.5 text-sm">
                        <div className="flex items-center gap-2">
                          <span
                            className={cn(
                              'flex h-5 w-5 items-center justify-center rounded-full',
                              u.flow === 'inflow'
                                ? 'bg-emerald-100 text-emerald-600'
                                : 'bg-red-100 text-red-600',
                            )}
                          >
                            {u.flow === 'inflow' ? (
                              <ArrowDownLeft className="h-3 w-3" />
                            ) : (
                              <ArrowUpRight className="h-3 w-3" />
                            )}
                          </span>
                          <span>{u.merchant || '—'}</span>
                          <span className="text-xs text-slate-400">{formatDate(u.date)}</span>
                        </div>
                        <MoneyText cents={u.amount_cents} colorize />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Subscriptions & bills</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {recurringQ.isLoading ? (
              <CenteredSpinner />
            ) : outflows.length === 0 ? (
              <p className="p-5 text-sm text-slate-400">No recurring charges detected yet.</p>
            ) : (
              <div className="divide-y divide-slate-100">
                {outflows.map((s) => (
                  <StreamRow key={s.id} s={s} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recurring income</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {recurringQ.isLoading ? (
              <CenteredSpinner />
            ) : inflows.length === 0 ? (
              <p className="p-5 text-sm text-slate-400">No recurring income detected yet.</p>
            ) : (
              <div className="divide-y divide-slate-100">
                {inflows.map((s) => (
                  <StreamRow key={s.id} s={s} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
