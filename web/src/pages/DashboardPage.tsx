import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { CategoryBadge } from '@/components/CategoryBadge'
import { MoneyText } from '@/components/MoneyText'
import { CategoryBreakdownChart } from '@/components/charts/CategoryBreakdownChart'
import { SpendingTrendChart } from '@/components/charts/SpendingTrendChart'
import { CenteredSpinner } from '@/components/ui/spinner'
import { useAccounts, useTransactions } from '@/hooks/useApi'
import {
  computeNetWorth,
  monthSpendTotal,
  spendingByCategory,
  spendingTrend,
} from '@/lib/selectors'
import { currentMonthKey, formatDate, monthLabel } from '@/lib/utils'

export function DashboardPage() {
  const accountsQ = useAccounts()
  const txnsQ = useTransactions({ limit: 500 })
  const month = currentMonthKey()

  const accounts = accountsQ.data ?? []
  const txns = txnsQ.data ?? []

  const netWorth = useMemo(() => computeNetWorth(accounts), [accounts])
  const trend = useMemo(() => spendingTrend(txns, 3), [txns])
  const breakdown = useMemo(() => spendingByCategory(txns, month), [txns, month])
  const monthSpend = useMemo(() => monthSpendTotal(txns, month), [txns, month])
  const recent = useMemo(
    () => [...txns].sort((a, b) => (a.date < b.date ? 1 : -1)).slice(0, 5),
    [txns],
  )

  if (accountsQ.isLoading || txnsQ.isLoading) return <CenteredSpinner label="Loading dashboard…" />

  return (
    <div className="flex flex-col gap-6">
      <header>
        <p className="text-sm text-slate-500">Welcome back</p>
        <div className="mt-0.5 text-4xl font-bold tracking-tight">
          <MoneyText cents={netWorth.net_cents} />
        </div>
        <p className="mt-0.5 text-xs text-slate-400">
          Total net worth across {accounts.length} account{accounts.length === 1 ? '' : 's'}
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {accounts.length === 0 && (
          <p className="text-sm text-slate-400">
            No accounts yet — connect a bank on{' '}
            <Link to="/connections" className="underline">Connections</Link>.
          </p>
        )}
        {accounts.map((a) => (
          <Link
            key={a.id}
            to={`/accounts?account=${a.id}`}
            className="block rounded-xl border border-slate-200 bg-white p-[18px] hover:border-slate-300"
          >
            <div className="flex items-center justify-between">
              <span className="text-[13px] font-semibold text-slate-800">{a.name}</span>
              {a.mask && <span className="text-[11px] text-slate-400">•••• {a.mask}</span>}
            </div>
            <div className="mt-2.5 text-[22px] font-bold tracking-tight">
              <MoneyText cents={a.is_liability ? -a.balance_cents : a.balance_cents} colorize />
            </div>
            <span className="text-xs text-slate-400">{a.type}</span>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px] lg:items-start">
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-1 text-[13px] font-semibold uppercase tracking-wide text-slate-500">
            Income vs. spending
          </h2>
          <p className="mb-2 text-xs text-slate-400">Last 3 months</p>
          <SpendingTrendChart data={trend} />
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-1 text-[13px] font-semibold uppercase tracking-wide text-slate-500">
            {monthLabel(month)} spending
          </h2>
          <div className="text-2xl font-bold tracking-tight">
            <MoneyText cents={-monthSpend} colorize />
          </div>
          <CategoryBreakdownChart data={breakdown} />
        </section>
      </div>

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h2 className="text-[13px] font-semibold uppercase tracking-wide text-slate-500">
            Recent activity
          </h2>
          <Link to="/transactions" className="text-[13px] font-medium text-sky-500 hover:underline">
            View all →
          </Link>
        </div>
        {recent.length === 0 && (
          <p className="px-5 py-6 text-sm text-slate-400">No transactions yet.</p>
        )}
        {recent.map((tx) => (
          <Link
            key={tx.id}
            to={`/transactions/${tx.id}`}
            className="grid grid-cols-[84px_1fr_auto_auto] items-center gap-4 border-t border-slate-100 px-5 py-3.5 text-inherit hover:bg-slate-50"
          >
            <span className="text-xs tabular-nums text-slate-400">{formatDate(tx.date)}</span>
            <span className="truncate text-sm font-medium text-slate-800">
              {tx.merchant || tx.raw_name || '—'}
            </span>
            <CategoryBadge category={tx.category} />
            <span className="min-w-[88px] text-right text-sm font-semibold">
              <MoneyText cents={tx.amount_cents} colorize />
            </span>
          </Link>
        ))}
      </section>
    </div>
  )
}
