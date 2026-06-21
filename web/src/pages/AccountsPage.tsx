import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { CategoryBadge } from '@/components/CategoryBadge'
import { MoneyText } from '@/components/MoneyText'
import { SpendingTrendChart } from '@/components/charts/SpendingTrendChart'
import { Badge } from '@/components/ui/badge'
import { Select } from '@/components/ui/select'
import { CenteredSpinner } from '@/components/ui/spinner'
import { useAccounts, useTransactions } from '@/hooks/useApi'
import { spendingTrend } from '@/lib/selectors'
import { formatDate } from '@/lib/utils'

export function AccountsPage() {
  const accountsQ = useAccounts()
  const [params, setParams] = useSearchParams()
  const accounts = accountsQ.data ?? []
  const selectedId = params.get('account') ?? accounts[0]?.id ?? ''
  const account = accounts.find((a) => a.id === selectedId) ?? accounts[0]
  const txnsQ = useTransactions(account ? { account_id: account.id, limit: 500 } : { limit: 1 })

  const txns = useMemo(
    () => [...(txnsQ.data ?? [])].sort((a, b) => (a.date < b.date ? 1 : -1)),
    [txnsQ.data],
  )
  const trend = useMemo(() => spendingTrend(txnsQ.data ?? [], 3), [txnsQ.data])

  if (accountsQ.isLoading) return <CenteredSpinner label="Loading accounts…" />
  if (!account) {
    return (
      <p className="text-sm text-slate-400">
        No accounts yet — connect a bank on{' '}
        <Link to="/connections" className="underline">
          Connections
        </Link>
        .
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-xl font-semibold">Accounts</h1>
        <Select value={account.id} onChange={(e) => setParams({ account: e.target.value })}>
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
              {a.mask ? ` ••••${a.mask}` : ''}
            </option>
          ))}
        </Select>
      </div>

      <header className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="flex items-center gap-2.5">
          <h2 className="text-[22px] font-semibold tracking-tight">{account.name}</h2>
          <Badge className="bg-slate-100 text-slate-600">{account.type}</Badge>
        </div>
        {account.mask && (
          <p className="mt-1 text-[13px] text-slate-400">•••• •••• •••• {account.mask}</p>
        )}
        <div className="mt-3.5 text-4xl font-bold tracking-tight">
          <MoneyText
            cents={account.is_liability ? -account.balance_cents : account.balance_cents}
            colorize
          />
        </div>
        <p className="mt-0.5 text-xs text-slate-400">
          {account.is_liability ? 'Current balance owed' : 'Available balance'}
        </p>
      </header>

      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="mb-2 text-[13px] font-semibold uppercase tracking-wide text-slate-500">
          Activity · last 3 months
        </h2>
        <SpendingTrendChart data={trend} />
      </section>

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <div className="border-b border-slate-100 px-5 py-4">
          <h2 className="text-[13px] font-semibold uppercase tracking-wide text-slate-500">
            Transactions · {txns.length}
          </h2>
        </div>
        {txnsQ.isLoading ? (
          <CenteredSpinner label="Loading transactions…" />
        ) : txns.length === 0 ? (
          <p className="px-5 py-6 text-sm text-slate-400">No transactions for this account.</p>
        ) : (
          txns.map((tx) => (
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
          ))
        )}
      </section>
    </div>
  )
}
