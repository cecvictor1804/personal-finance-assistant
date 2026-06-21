// Pure client-side aggregations for the dashboard. (Phase 3 will move these to precomputed
// Firestore `rollups` for cheaper reads; for now we compute from the transaction list.)

import type { Account, Category, Transaction } from '@/types'
import { CATEGORY_COLORS, categoryLabel } from './categories'
import { monthKey, monthLabel } from './utils'

export interface NetWorth {
  assets_cents: number
  liabilities_cents: number
  net_cents: number
}

export function computeNetWorth(accounts: Account[]): NetWorth {
  let assets = 0
  let liabilities = 0
  for (const a of accounts) {
    if (a.is_liability) liabilities += a.balance_cents
    else assets += a.balance_cents
  }
  return { assets_cents: assets, liabilities_cents: liabilities, net_cents: assets - liabilities }
}

const isSpend = (t: Transaction) => t.amount_cents < 0 && !t.is_transfer && t.category !== 'INCOME'
const isIncome = (t: Transaction) => t.amount_cents > 0 && !t.is_transfer

export interface CategoryDatum {
  category: Category
  label: string
  value_cents: number
  color: string
}

export function spendingByCategory(txns: Transaction[], month: string): CategoryDatum[] {
  const totals = new Map<Category, number>()
  for (const t of txns) {
    if (monthKey(t.date) !== month || !isSpend(t)) continue
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

export interface TrendDatum {
  month: string // label, e.g. "Jun 26"
  spending_cents: number
  income_cents: number
}

export function spendingTrend(txns: Transaction[], months = 6): TrendDatum[] {
  const now = new Date()
  const keys: string[] = []
  for (let i = months - 1; i >= 0; i--) {
    keys.push(monthKey(new Date(now.getFullYear(), now.getMonth() - i, 1)))
  }
  const byKey = new Map<string, TrendDatum>(
    keys.map((k) => [k, { month: monthLabel(k), spending_cents: 0, income_cents: 0 }]),
  )
  for (const t of txns) {
    const k = monthKey(t.date)
    const row = byKey.get(k)
    if (!row) continue
    if (isSpend(t)) row.spending_cents += Math.abs(t.amount_cents)
    else if (isIncome(t)) row.income_cents += t.amount_cents
  }
  return keys.map((k) => byKey.get(k)!)
}

export function monthSpendTotal(txns: Transaction[], month: string): number {
  return txns.reduce(
    (sum, t) => (monthKey(t.date) === month && isSpend(t) ? sum + Math.abs(t.amount_cents) : sum),
    0,
  )
}

export function monthIncomeTotal(txns: Transaction[], month: string): number {
  return txns.reduce(
    (sum, t) => (monthKey(t.date) === month && isIncome(t) ? sum + t.amount_cents : sum),
    0,
  )
}
