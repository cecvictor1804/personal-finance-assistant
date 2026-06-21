import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, Plus } from 'lucide-react'
import { CategoryBadge } from '@/components/CategoryBadge'
import { MoneyText } from '@/components/MoneyText'
import { CategoryBreakdownChart } from '@/components/charts/CategoryBreakdownChart'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { CenteredSpinner } from '@/components/ui/spinner'
import { useCreateManualTransaction, useTransactions } from '@/hooks/useApi'
import { CATEGORY_COLORS, CATEGORY_OPTIONS, categoryLabel } from '@/lib/categories'
import { formatDate } from '@/lib/utils'
import type { Category, Transaction } from '@/types'

function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

function ManualEntryForm({ onDone }: { onDone: () => void }) {
  const create = useCreateManualTransaction()
  const [merchant, setMerchant] = useState('')
  const [amount, setAmount] = useState('')
  const [date, setDate] = useState(todayIso())
  const [kind, setKind] = useState<'expense' | 'income'>('expense')
  const [category, setCategory] = useState<Category | ''>('')
  const [account, setAccount] = useState('cash')

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const dollars = Math.round(Number(amount) * 100)
    if (!Number.isFinite(dollars) || dollars <= 0) return
    create.mutate(
      {
        account_id: account || 'cash',
        amount_cents: kind === 'expense' ? -dollars : dollars,
        date,
        merchant,
        category: category || undefined,
      },
      {
        onSuccess: () => {
          setMerchant('')
          setAmount('')
          onDone()
        },
      },
    )
  }

  return (
    <form onSubmit={submit} className="grid grid-cols-2 gap-3 sm:grid-cols-6">
      <Input
        className="col-span-2"
        placeholder="Merchant"
        value={merchant}
        onChange={(e) => setMerchant(e.target.value)}
      />
      <Input
        type="number"
        step="0.01"
        min="0"
        placeholder="0.00"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
      />
      <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      <Select value={kind} onChange={(e) => setKind(e.target.value as 'expense' | 'income')}>
        <option value="expense">Expense</option>
        <option value="income">Income</option>
      </Select>
      <Select value={category} onChange={(e) => setCategory(e.target.value as Category)}>
        <option value="">Auto-categorize</option>
        {CATEGORY_OPTIONS.map((c) => (
          <option key={c} value={c}>
            {categoryLabel(c)}
          </option>
        ))}
      </Select>
      <div className="col-span-2 flex items-center gap-2 sm:col-span-6">
        <Input
          className="max-w-[160px]"
          placeholder="Account id"
          value={account}
          onChange={(e) => setAccount(e.target.value)}
        />
        <Button type="submit" disabled={create.isPending}>
          Add transaction
        </Button>
        {create.isError && (
          <span className="text-xs text-red-600">{(create.error as Error).message}</span>
        )}
      </div>
    </form>
  )
}

const isSpend = (t: Transaction): boolean =>
  t.amount_cents < 0 && !t.is_transfer && t.category !== 'INCOME'

interface Slice {
  category: Category
  label: string
  value_cents: number
  color: string
}

function breakdownOf(txns: Transaction[]): Slice[] {
  const totals = new Map<Category, number>()
  for (const t of txns) {
    if (!isSpend(t)) continue
    totals.set(t.category, (totals.get(t.category) ?? 0) + Math.abs(t.amount_cents))
  }
  return [...totals.entries()]
    .map(([category, value_cents]) => ({
      category,
      label: categoryLabel(category),
      value_cents,
      color: CATEGORY_COLORS[category],
    }))
    .sort((a, b) => b.value_cents - a.value_cents)
}

export function TransactionsPage() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<Category | 'ALL'>('ALL')
  const [showForm, setShowForm] = useState(false)
  const txnsQ = useTransactions({ limit: 500 })
  const all = txnsQ.data ?? []

  const q = query.toLowerCase().trim()
  const filtered = useMemo(
    () =>
      all.filter(
        (t) =>
          (category === 'ALL' || t.category === category) &&
          (!q || (t.merchant || t.raw_name || '').toLowerCase().includes(q)),
      ),
    [all, category, q],
  )
  const breakdown = useMemo(() => breakdownOf(filtered), [filtered])
  const totalSpent = breakdown.reduce((s, d) => s + d.value_cents, 0)
  const topCats = breakdown.slice(0, 6)

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-semibold tracking-tight">Transactions</h1>
          <p className="mt-1 text-sm text-slate-500">{filtered.length} shown</p>
        </div>
        <Button size="sm" onClick={() => setShowForm((s) => !s)}>
          <Plus className="h-4 w-4" />
          Manual entry
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Add a manual transaction</CardTitle>
          </CardHeader>
          <CardContent>
            <ManualEntryForm onDone={() => setShowForm(false)} />
          </CardContent>
        </Card>
      )}

      <div className="flex flex-wrap gap-3">
        <div className="min-w-[220px] flex-1">
          <Input
            type="search"
            placeholder="Search merchant…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <Select value={category} onChange={(e) => setCategory(e.target.value as Category | 'ALL')}>
          <option value="ALL">All categories</option>
          {CATEGORY_OPTIONS.map((c) => (
            <option key={c} value={c}>
              {categoryLabel(c)}
            </option>
          ))}
        </Select>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px] lg:items-start">
        <section className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          {txnsQ.isLoading ? (
            <CenteredSpinner label="Loading transactions…" />
          ) : filtered.length === 0 ? (
            <div className="px-6 py-14 text-center text-sm text-slate-400">
              No transactions match your filters.
            </div>
          ) : (
            filtered.map((tx) => (
              <Link
                key={tx.id}
                to={`/transactions/${tx.id}`}
                className="grid grid-cols-[84px_1fr_auto_auto] items-center gap-4 border-t border-slate-100 px-5 py-3.5 text-inherit first:border-t-0 hover:bg-slate-50"
              >
                <span className="text-xs tabular-nums text-slate-400">{formatDate(tx.date)}</span>
                <div className="min-w-0">
                  <span className="block truncate text-sm font-medium text-slate-800">
                    {tx.merchant || tx.raw_name || '—'}
                  </span>
                  {(tx.pending || tx.possible_duplicate_of) && (
                    <span className="mt-0.5 flex items-center gap-1.5">
                      {tx.pending && (
                        <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] text-amber-700">
                          pending
                        </span>
                      )}
                      {tx.possible_duplicate_of && (
                        <span className="inline-flex items-center gap-1 rounded bg-orange-100 px-1.5 py-0.5 text-[10px] text-orange-700">
                          <AlertTriangle className="h-3 w-3" />
                          possible duplicate
                        </span>
                      )}
                    </span>
                  )}
                </div>
                <CategoryBadge category={tx.category} />
                <span className="min-w-[88px] text-right text-sm font-semibold">
                  <MoneyText cents={tx.amount_cents} colorize />
                </span>
              </Link>
            ))
          )}
        </section>

        <aside className="rounded-xl border border-slate-200 bg-white p-5 lg:sticky lg:top-6">
          <h2 className="text-[13px] font-semibold uppercase tracking-wide text-slate-500">
            Spending summary
          </h2>
          <div className="my-1 text-3xl font-bold tracking-tight">
            <MoneyText cents={-totalSpent} colorize />
          </div>
          <p className="mb-2 text-xs text-slate-400">
            Total spent · {category === 'ALL' ? 'All' : categoryLabel(category)}
          </p>

          <CategoryBreakdownChart data={breakdown} />

          <div className="mt-2 flex flex-col">
            {topCats.map((c) => (
              <div key={c.category} className="flex items-center gap-2 py-1.5 text-[13px]">
                <span
                  className="h-[9px] w-[9px] flex-none rounded-full"
                  style={{ background: c.color }}
                />
                <span className="flex-1 truncate text-slate-700">{c.label}</span>
                <span className="font-semibold tabular-nums">
                  <MoneyText cents={c.value_cents} />
                </span>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  )
}
