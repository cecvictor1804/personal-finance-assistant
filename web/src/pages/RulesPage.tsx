import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { CategoryBadge } from '@/components/CategoryBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { CenteredSpinner } from '@/components/ui/spinner'
import { useCreateRule, useDeleteRule, useRules } from '@/hooks/useApi'
import { CATEGORY_OPTIONS, categoryLabel } from '@/lib/categories'
import type { Category, MatchType } from '@/types'

export function RulesPage() {
  const rulesQ = useRules()
  const create = useCreateRule()
  const del = useDeleteRule()

  const [matchType, setMatchType] = useState<MatchType>('contains')
  const [pattern, setPattern] = useState('')
  const [category, setCategory] = useState<Category>('GROCERIES')
  const [priority, setPriority] = useState('100')

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!pattern.trim()) return
    create.mutate(
      { match_type: matchType, pattern: pattern.trim(), category, priority: Number(priority) || 100 },
      { onSuccess: () => setPattern('') },
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">Categorization rules</h1>
      <p className="text-sm text-slate-500">
        Rules run before Plaid’s category — lower priority numbers win. Recategorizing a transaction
        also creates a rule automatically.
      </p>

      <Card>
        <CardHeader>
          <CardTitle>Add a rule</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            <Select value={matchType} onChange={(e) => setMatchType(e.target.value as MatchType)}>
              <option value="contains">contains</option>
              <option value="equals">equals</option>
              <option value="regex">regex</option>
            </Select>
            <Input
              className="col-span-2"
              placeholder="Merchant pattern (e.g. starbucks)"
              value={pattern}
              onChange={(e) => setPattern(e.target.value)}
            />
            <Select value={category} onChange={(e) => setCategory(e.target.value as Category)}>
              {CATEGORY_OPTIONS.map((c) => (
                <option key={c} value={c}>
                  {categoryLabel(c)}
                </option>
              ))}
            </Select>
            <Input
              type="number"
              placeholder="Priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
            />
            <Button type="submit" disabled={create.isPending} className="col-span-2 sm:col-span-1">
              Add rule
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {rulesQ.isLoading ? (
            <CenteredSpinner label="Loading rules…" />
          ) : (rulesQ.data ?? []).length === 0 ? (
            <p className="p-6 text-sm text-slate-400">No rules yet.</p>
          ) : (
            <div className="divide-y divide-slate-100">
              {(rulesQ.data ?? []).map((r) => (
                <div key={r.id} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500">
                      #{r.priority}
                    </span>
                    <span className="text-slate-500">{r.match_type}</span>
                    <span className="font-mono">{r.pattern}</span>
                    <span className="text-slate-400">→</span>
                    <CategoryBadge category={r.category} />
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => del.mutate(r.id)}
                    disabled={del.isPending}
                  >
                    <Trash2 className="h-4 w-4 text-slate-400" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
