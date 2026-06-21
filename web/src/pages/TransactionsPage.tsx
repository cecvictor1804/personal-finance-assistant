import { useState } from 'react'
import { AlertTriangle, Plus } from 'lucide-react'
import { CategoryBadge } from '@/components/CategoryBadge'
import { MoneyText } from '@/components/MoneyText'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { CenteredSpinner } from '@/components/ui/spinner'
import { useCreateManualTransaction, useRecategorize, useTransactions } from '@/hooks/useApi'
import { CATEGORY_OPTIONS, categoryLabel } from '@/lib/categories'
import { formatDate } from '@/lib/utils'
import type { Category } from '@/types'

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

export function TransactionsPage() {
  const [filter, setFilter] = useState<Category | ''>('')
  const [showForm, setShowForm] = useState(false)
  const txnsQ = useTransactions({ limit: 200, category: filter || undefined })
  const recategorize = useRecategorize()

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Transactions</h1>
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

      <div className="flex items-center gap-2">
        <span className="text-sm text-slate-500">Filter:</span>
        <Select value={filter} onChange={(e) => setFilter(e.target.value as Category)}>
          <option value="">All categories</option>
          {CATEGORY_OPTIONS.map((c) => (
            <option key={c} value={c}>
              {categoryLabel(c)}
            </option>
          ))}
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          {txnsQ.isLoading ? (
            <CenteredSpinner label="Loading transactions…" />
          ) : (txnsQ.data ?? []).length === 0 ? (
            <p className="p-6 text-sm text-slate-400">No transactions match.</p>
          ) : (
            <div className="divide-y divide-slate-100">
              {(txnsQ.data ?? []).map((t) => (
                <div key={t.id} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate font-medium">
                        {t.merchant || t.raw_name || '—'}
                      </span>
                      {t.pending && (
                        <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] text-amber-700">
                          pending
                        </span>
                      )}
                      {t.possible_duplicate_of && (
                        <span
                          className="inline-flex items-center gap-1 rounded bg-orange-100 px-1.5 py-0.5 text-[10px] text-orange-700"
                          title="Looks like a manual entry you already logged"
                        >
                          <AlertTriangle className="h-3 w-3" />
                          possible duplicate
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400">
                      {formatDate(t.date)} · {t.source}
                    </div>
                  </div>

                  <div className="hidden sm:block">
                    <CategoryBadge category={t.category} />
                  </div>

                  <Select
                    className="w-40"
                    value={t.category}
                    disabled={recategorize.isPending}
                    onChange={(e) =>
                      recategorize.mutate({ id: t.id, category: e.target.value as Category })
                    }
                  >
                    {CATEGORY_OPTIONS.map((c) => (
                      <option key={c} value={c}>
                        {categoryLabel(c)}
                      </option>
                    ))}
                  </Select>

                  <MoneyText cents={t.amount_cents} colorize className="w-24 text-right" />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
