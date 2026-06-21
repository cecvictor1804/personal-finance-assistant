import { useEffect, useState } from 'react'
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

function barColor(pct: number): string {
  if (pct >= 100) return 'bg-red-500'
  if (pct >= 80) return 'bg-amber-500'
  return 'bg-emerald-500'
}

export function BudgetsPage() {
  const month = currentMonthKey()
  const budgetQ = useBudget(month)
  const save = useSetBudgetCaps(month)

  // Editable caps in dollars, keyed by category.
  const [caps, setCaps] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!budgetQ.data) return
    const next: Record<string, string> = {}
    for (const [cat, cents] of Object.entries(budgetQ.data.caps_cents)) {
      next[cat] = (cents / 100).toString()
    }
    setCaps(next)
  }, [budgetQ.data])

  if (budgetQ.isLoading || !budgetQ.data) return <CenteredSpinner label="Loading budgets…" />

  const spent = budgetQ.data.spent_cents

  const onSave = () => {
    const caps_cents: Record<string, number> = {}
    for (const [cat, val] of Object.entries(caps)) {
      const cents = Math.round(Number(val) * 100)
      if (Number.isFinite(cents) && cents > 0) caps_cents[cat] = cents
    }
    save.mutate(caps_cents)
  }

  // Sort: categories with a cap or spend first, by spend desc.
  const rows = [...BUDGETABLE].sort((a, b) => (spent[b] ?? 0) - (spent[a] ?? 0))

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Budgets</h1>
          <p className="text-sm text-slate-500">{monthLabel(month)} · monthly category caps</p>
        </div>
        <Button onClick={onSave} disabled={save.isPending}>
          {save.isPending ? 'Saving…' : 'Save budgets'}
        </Button>
      </div>

      {save.isError && (
        <div className="rounded-md bg-red-50 px-4 py-2 text-sm text-red-700">
          {(save.error as Error).message}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Category budgets</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {rows.map((cat) => {
            const spentCents = spent[cat] ?? 0
            const capCents = Math.round(Number(caps[cat] ?? '0') * 100)
            const pct = capCents > 0 ? (spentCents / capCents) * 100 : 0
            return (
              <div key={cat} className="grid grid-cols-12 items-center gap-3">
                <div className="col-span-4 text-sm font-medium sm:col-span-3">
                  {categoryLabel(cat as Category)}
                </div>
                <div className="col-span-5 sm:col-span-6">
                  <Progress value={pct} barClassName={capCents > 0 ? barColor(pct) : 'bg-slate-200'} />
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
    </div>
  )
}
