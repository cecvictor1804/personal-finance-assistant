import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { CategoryBadge } from '@/components/CategoryBadge'
import { MoneyText } from '@/components/MoneyText'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { CenteredSpinner } from '@/components/ui/spinner'
import { useAccounts, useRecategorize, useTransaction, useTransactions } from '@/hooks/useApi'
import { CATEGORY_OPTIONS, categoryLabel } from '@/lib/categories'
import { formatDate } from '@/lib/utils'
import type { Category } from '@/types'

export function TransactionDetailPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const txnQ = useTransaction(id)
  const listQ = useTransactions({ limit: 200 })
  const accountsQ = useAccounts()
  const recategorize = useRecategorize()

  const tx = txnQ.data
  const [note, setNote] = useState('')
  useEffect(() => {
    setNote(tx?.notes ?? '')
  }, [tx])

  if (txnQ.isLoading) return <CenteredSpinner label="Loading transaction…" />
  if (!tx) {
    return (
      <p className="text-sm text-slate-400">
        Transaction not found.{' '}
        <Link to="/transactions" className="underline">
          Back to transactions
        </Link>
      </p>
    )
  }

  const account = (accountsQ.data ?? []).find((a) => a.id === tx.account_id)
  const options = [...(listQ.data ?? [])].sort((a, b) => (a.date < b.date ? 1 : -1))

  return (
    <div className="mx-auto flex max-w-[640px] flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <Link to="/transactions" className="text-[13px] text-slate-500 hover:text-slate-900">
          ← Transactions
        </Link>
        {options.length > 0 && (
          <Select value={tx.id} onChange={(e) => navigate(`/transactions/${e.target.value}`)}>
            {options.map((o) => (
              <option key={o.id} value={o.id}>
                {formatDate(o.date)} · {o.merchant || o.raw_name || '—'}
              </option>
            ))}
          </Select>
        )}
      </div>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <div className="border-b border-slate-100 px-6 py-7 text-center">
          <div className="text-[46px] font-bold tracking-tight">
            <MoneyText cents={tx.amount_cents} colorize />
          </div>
          <h1 className="mt-2.5 text-lg font-semibold">{tx.merchant || tx.raw_name || '—'}</h1>
          <p className="mt-1 text-[13px] text-slate-400">{formatDate(tx.date)}</p>
          <div className="mt-3 flex justify-center">
            <CategoryBadge category={tx.category} />
          </div>
        </div>

        <div className="px-6 py-2">
          <div className="flex items-center justify-between border-b border-slate-100 py-3.5">
            <span className="text-[13px] text-slate-500">Account</span>
            <span className="text-sm font-medium">
              {account ? `${account.name}${account.mask ? ` ••••${account.mask}` : ''}` : tx.account_id}
            </span>
          </div>
          <div className="flex items-center justify-between border-b border-slate-100 py-3.5">
            <span className="text-[13px] text-slate-500">Status</span>
            {tx.pending ? (
              <Badge className="bg-amber-100 text-amber-700">Pending</Badge>
            ) : (
              <Badge className="bg-emerald-100 text-emerald-700">Posted</Badge>
            )}
          </div>
          {tx.possible_duplicate_of && (
            <div className="flex items-center justify-between border-b border-slate-100 py-3.5">
              <span className="text-[13px] text-slate-500">Flag</span>
              <Badge className="bg-orange-100 text-orange-700">Possible duplicate</Badge>
            </div>
          )}
          <div className="flex items-center justify-between gap-4 border-b border-slate-100 py-3.5">
            <span className="text-[13px] text-slate-500">Category</span>
            <div className="w-[220px]">
              <Select
                className="w-full"
                value={tx.category}
                disabled={recategorize.isPending}
                onChange={(e) =>
                  recategorize.mutate({ id: tx.id, category: e.target.value as Category })
                }
              >
                {CATEGORY_OPTIONS.map((c) => (
                  <option key={c} value={c}>
                    {categoryLabel(c)}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          <div className="py-3.5">
            <span className="mb-2 block text-[13px] text-slate-500">Note</span>
            <Input placeholder="Add a note…" value={note} onChange={(e) => setNote(e.target.value)} />
            <p className="mt-1 text-[11px] text-slate-400">
              Changing the category saves immediately. Note editing isn’t persisted yet.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
