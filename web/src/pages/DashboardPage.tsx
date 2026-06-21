import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { CategoryBadge } from '@/components/CategoryBadge'
import { MoneyText } from '@/components/MoneyText'
import { CategoryBreakdownChart } from '@/components/charts/CategoryBreakdownChart'
import { SpendingTrendChart } from '@/components/charts/SpendingTrendChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { CenteredSpinner } from '@/components/ui/spinner'
import { categoryLabel } from '@/lib/categories'
import { useAccounts, useBudget, useTransactions } from '@/hooks/useApi'
import type { Category } from '@/types'
import {
  computeNetWorth,
  monthIncomeTotal,
  monthSpendTotal,
  spendingByCategory,
  spendingTrend,
} from '@/lib/selectors'
import { currentMonthKey, formatDate } from '@/lib/utils'

function StatCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="text-2xl font-semibold">{children}</CardContent>
    </Card>
  )
}

function budgetBarColor(pct: number): string {
  if (pct >= 100) return 'bg-red-500'
  if (pct >= 80) return 'bg-amber-500'
  return 'bg-emerald-500'
}

export function DashboardPage() {
  const accountsQ = useAccounts()
  const txnsQ = useTransactions({ limit: 500 })
  const month = currentMonthKey()
  const budgetQ = useBudget(month)
  const accounts = accountsQ.data ?? []
  const txns = txnsQ.data ?? []

  const netWorth = useMemo(() => computeNetWorth(accounts), [accounts])
  const trend = useMemo(() => spendingTrend(txns, 6), [txns])
  const byCategory = useMemo(() => spendingByCategory(txns, month), [txns, month])
  const spend = useMemo(() => monthSpendTotal(txns, month), [txns, month])
  const income = useMemo(() => monthIncomeTotal(txns, month), [txns, month])
  const recent = useMemo(
    () => [...txns].sort((a, b) => (a.date < b.date ? 1 : -1)).slice(0, 8),
    [txns],
  )
  const budgetRows = useMemo(() => {
    const b = budgetQ.data
    if (!b) return []
    return Object.entries(b.caps_cents)
      .map(([cat, cap]) => ({ cat: cat as Category, cap, spent: b.spent_cents[cat] ?? 0 }))
      .sort((x, y) => y.spent / y.cap - x.spent / x.cap)
      .slice(0, 6)
  }, [budgetQ.data])

  if (accountsQ.isLoading || txnsQ.isLoading) return <CenteredSpinner label="Loading dashboard…" />

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">Dashboard</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Net worth">
          <MoneyText cents={netWorth.net_cents} colorize />
        </StatCard>
        <StatCard title="Assets">
          <MoneyText cents={netWorth.assets_cents} />
        </StatCard>
        <StatCard title="Spending this month">
          <MoneyText cents={spend} />
        </StatCard>
        <StatCard title="Income this month">
          <MoneyText cents={income} />
        </StatCard>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Spending vs income (6 months)</CardTitle>
          </CardHeader>
          <CardContent>
            <SpendingTrendChart data={trend} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>This month by category</CardTitle>
          </CardHeader>
          <CardContent>
            <CategoryBreakdownChart data={byCategory} />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Accounts</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {accounts.length === 0 && (
              <p className="text-sm text-slate-400">No accounts yet — connect a bank.</p>
            )}
            {accounts.map((a) => (
              <div key={a.id} className="flex items-center justify-between text-sm">
                <div>
                  <div className="font-medium">{a.name}</div>
                  <div className="text-xs text-slate-400">
                    {a.type}
                    {a.mask ? ` ••${a.mask}` : ''}
                  </div>
                </div>
                <MoneyText cents={a.is_liability ? -a.balance_cents : a.balance_cents} colorize />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Recent transactions</CardTitle>
            <Link to="/transactions" className="text-xs font-medium text-slate-500 hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent className="flex flex-col divide-y divide-slate-100">
            {recent.length === 0 && (
              <p className="py-4 text-sm text-slate-400">No transactions yet.</p>
            )}
            {recent.map((t) => (
              <div key={t.id} className="flex items-center justify-between gap-3 py-2 text-sm">
                <div className="min-w-0">
                  <div className="truncate font-medium">{t.merchant || t.raw_name || '—'}</div>
                  <div className="text-xs text-slate-400">{formatDate(t.date)}</div>
                </div>
                <div className="flex items-center gap-3">
                  <CategoryBadge category={t.category} />
                  <MoneyText cents={t.amount_cents} colorize className="w-24 text-right" />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>Budgets this month</CardTitle>
          <Link to="/budgets" className="text-xs font-medium text-slate-500 hover:underline">
            Manage
          </Link>
        </CardHeader>
        <CardContent>
          {budgetRows.length === 0 ? (
            <p className="text-sm text-slate-400">
              No budgets set yet. <Link to="/budgets" className="underline">Create some</Link> to
              track spending against caps.
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {budgetRows.map(({ cat, cap, spent }) => {
                const pct = cap > 0 ? (spent / cap) * 100 : 0
                return (
                  <div key={cat}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="font-medium">{categoryLabel(cat)}</span>
                      <span className="text-slate-500">
                        <MoneyText cents={spent} /> / <MoneyText cents={cap} />
                      </span>
                    </div>
                    <Progress value={pct} barClassName={budgetBarColor(pct)} />
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
