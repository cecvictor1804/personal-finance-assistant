import { useEffect, useMemo, useState } from 'react'
import { CategoryBadge } from '@/components/CategoryBadge'
import { MoneyText } from '@/components/MoneyText'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { CenteredSpinner } from '@/components/ui/spinner'
import { useBudget, useSetBudgetCaps } from '@/hooks/useApi'
import { CATEGORY_OPTIONS, categoryLabel } from '@/lib/categories'
import { currentMonthKey, formatCents, monthLabel } from '@/lib/utils'
import type { Category } from '@/types'

// Budgets apply to spending categories only.
const BUDGETABLE = CATEGORY_OPTIONS.filter((c) => c !== 'INCOME' && c !== 'TRANSFER')

// Derive bar color + status label from spent vs. limit.
function statusOf(spent: number, limit: number) {
  const pct = limit > 0 ? Math.round((spent / limit) * 100) : 0
  const over = spent > limit
  const near = !over && pct >= 80
  return {
    pct: Math.min(100, pct),
    bar: over ? 'bg-red-500' : near ? 'bg-amber-500' : 'bg-emerald-500',
    label: over ? 'Over budget' : near ? 'Near limit' : 'On track',
    color: over ? 'text-red-600' : near ? 'text-amber-600' : 'text-emerald-600',
  }
}

export function BudgetsPage() {
  const month = currentMonthKey()
  const budgetQ = useBudget(month)
  const save = useSetBudgetCaps(month)
  const [editing, setEditing] = useState(false)
  const [caps, setCaps] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!budgetQ.data) return
    const next: Record<string, string> = {}
    for (const [cat, cents] of Object.entries(budgetQ.data.caps_cents)) {
      next[cat] = (cents / 100).toString()
    }
    setCaps(next)
  }, [budgetQ.data])

  const rows = useMemo(() => {
    const b = budgetQ.data
    if (!b) return []
    return Object.entries(b.caps_cents)
      .map(([cat, limit]) => {
        const spent = b.spent_cents[cat] ?? 0
        return { category: cat as Category, limit, spent, ...statusOf(spent, limit) }
      })
      .sort((a, c) => c.pct - a.pct)
  }, [budgetQ.data])

  if (budgetQ.isLoading || !budgetQ.data) return <CenteredSpinner label="Loading budgets…" />

  const spent = budgetQ.data.spent_cents
  const totalSpent = rows.reduce((s, b) => s + b.spent, 0)
  const totalLimit = rows.reduce((s, b) => s + b.limit, 0)
  const overall = statusOf(totalSpent, totalLimit)
  const overallBar =
    totalSpent > totalLimit ? 'bg-red-500' : overall.bar === 'bg-emerald-500' ? 'bg-slate-900' : overall.bar
  const overallPct = totalLimit > 0 ? Math.round((totalSpent / totalLimit) * 100) : 0

  const onSave = () => {
    const caps_cents: Record<string, number> = {}
    for (const [cat, val] of Object.entries(caps)) {
      const cents = Math.round(Number(val) * 100)
      if (Number.isFinite(cents) && cents > 0) caps_cents[cat] = cents
    }
    save.mutate(caps_cents, { onSuccess: () => setEditing(false) })
  }
  const editRows = [...BUDGETABLE].sort((a, b) => (spent[b] ?? 0) - (spent[a] ?? 0))

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-semibold tracking-tight">Budgets</h1>
          <p className="mt-1 text-sm text-slate-500">{monthLabel(month)} · monthly category caps</p>
        </div>
        {editing ? (
          <div className="flex gap-2">
            <Button variant="ghost" onClick={() => setEditing(false)} disabled={save.isPending}>
              Cancel
            </Button>
            <Button onClick={onSave} disabled={save.isPending}>
              {save.isPending ? 'Saving…' : 'Save budgets'}
            </Button>
          </div>
        ) : (
          <Button variant="outline" onClick={() => setEditing(true)}>
            Edit budgets
          </Button>
        )}
      </div>

      {save.isError && (
        <div className="rounded-md bg-red-50 px-4 py-2 text-sm text-red-700">
          {(save.error as Error).message}
        </div>
      )}

      {editing ? (
        <Card>
          <CardHeader>
            <CardTitle>Category caps</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {editRows.map((cat) => {
              const spentCents = spent[cat] ?? 0
              const capCents = Math.round(Number(caps[cat] ?? '0') * 100)
              const pct = capCents > 0 ? (spentCents / capCents) * 100 : 0
              return (
                <div key={cat} className="grid grid-cols-12 items-center gap-3">
                  <div className="col-span-4 text-sm font-medium sm:col-span-3">
                    {categoryLabel(cat as Category)}
                  </div>
                  <div className="col-span-5 sm:col-span-6">
                    <Progress
                      value={pct}
                      barClassName={capCents > 0 ? statusOf(spentCents, capCents).bar : 'bg-slate-200'}
                    />
                    <div className="mt-1 text-xs text-slate-400">
                      {formatCents(spentCents)} spent
                      {capCents > 0 ? ` of ${formatCents(capCents)} (${Math.round(pct)}%)` : ' · no cap'}
                    </div>
                  </div>
                  <div className="col-span-3 flex items-center gap-1">
                    <span className="text-sm text-slate-400">$</span>
                    <Input
                      type="number"
                      min="0"
                      step="1"
                      placeholder="cap"
                      value={caps[cat] ?? ''}
                      onChange={(e) => setCaps((c) => ({ ...c, [cat]: e.target.value }))}
                    />
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>
      ) : rows.length === 0 ? (
        <Card>
          <CardContent className="px-6 py-14 text-center text-sm text-slate-400">
            No budgets set yet. Click{' '}
            <span className="font-medium text-slate-600">Edit budgets</span> to set monthly caps.
          </CardContent>
        </Card>
      ) : (
        <>
          <section className="rounded-xl border border-slate-200 bg-white p-5">
            <div className="mb-3 flex items-end justify-between">
              <div>
                <p className="text-[13px] font-semibold uppercase tracking-wide text-slate-500">
                  Total spent this month
                </p>
                <div className="mt-0.5 text-[28px] font-bold tracking-tight">
                  <MoneyText cents={totalSpent} />
                  <span className="text-[15px] font-medium text-slate-400"> of </span>
                  <span className="text-lg font-semibold text-slate-500">
                    <MoneyText cents={totalLimit} />
                  </span>
                </div>
              </div>
              <span className={`text-[13px] font-semibold ${overall.color}`}>{overallPct}% used</span>
            </div>
            <Progress value={overall.pct} barClassName={overallBar} />
          </section>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {rows.map((b) => (
              <div key={b.category} className="rounded-xl border border-slate-200 bg-white p-[18px]">
                <div className="mb-3 flex items-center justify-between">
                  <CategoryBadge category={b.category} />
                  <span className={`text-xs font-semibold ${b.color}`}>{b.label}</span>
                </div>
                <div className="mb-2.5 flex items-baseline gap-1.5">
                  <span className="text-xl font-bold tracking-tight">
                    <MoneyText cents={b.spent} />
                  </span>
                  <span className="text-[13px] text-slate-400">/</span>
                  <span className="text-[13px] text-slate-400">
                    <MoneyText cents={b.limit} />
                  </span>
                </div>
                <Progress value={b.pct} barClassName={b.bar} />
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
