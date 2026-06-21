import type { Category } from '@/types'

export const CATEGORY_LABELS: Record<Category, string> = {
  INCOME: 'Income',
  TRANSFER: 'Transfer',
  FOOD_DINING: 'Food & Dining',
  GROCERIES: 'Groceries',
  SHOPPING: 'Shopping',
  TRANSPORT: 'Transport',
  TRAVEL: 'Travel',
  BILLS_UTILITIES: 'Bills & Utilities',
  RENT_MORTGAGE: 'Rent / Mortgage',
  HEALTHCARE: 'Healthcare',
  ENTERTAINMENT: 'Entertainment',
  PERSONAL_CARE: 'Personal Care',
  EDUCATION: 'Education',
  FEES_CHARGES: 'Fees & Charges',
  LOAN_PAYMENT: 'Loan Payment',
  TAXES_GOV: 'Taxes & Government',
  GIFTS_DONATIONS: 'Gifts & Donations',
  BUSINESS_SERVICES: 'Business Services',
  UNCATEGORIZED: 'Uncategorized',
}

// Stable colors for charts/badges.
export const CATEGORY_COLORS: Record<Category, string> = {
  INCOME: '#16a34a',
  TRANSFER: '#64748b',
  FOOD_DINING: '#f97316',
  GROCERIES: '#84cc16',
  SHOPPING: '#ec4899',
  TRANSPORT: '#0ea5e9',
  TRAVEL: '#6366f1',
  BILLS_UTILITIES: '#eab308',
  RENT_MORTGAGE: '#ef4444',
  HEALTHCARE: '#14b8a6',
  ENTERTAINMENT: '#a855f7',
  PERSONAL_CARE: '#f43f5e',
  EDUCATION: '#3b82f6',
  FEES_CHARGES: '#9ca3af',
  LOAN_PAYMENT: '#dc2626',
  TAXES_GOV: '#78716c',
  GIFTS_DONATIONS: '#d946ef',
  BUSINESS_SERVICES: '#0891b2',
  UNCATEGORIZED: '#cbd5e1',
}

export const CATEGORY_OPTIONS = Object.keys(CATEGORY_LABELS) as Category[]

export function categoryLabel(c: Category): string {
  return CATEGORY_LABELS[c] ?? c
}
