// Mirrors the backend domain models (snake_case, as returned by the FastAPI API).

export type Category =
  | 'INCOME'
  | 'TRANSFER'
  | 'FOOD_DINING'
  | 'GROCERIES'
  | 'SHOPPING'
  | 'TRANSPORT'
  | 'TRAVEL'
  | 'BILLS_UTILITIES'
  | 'RENT_MORTGAGE'
  | 'HEALTHCARE'
  | 'ENTERTAINMENT'
  | 'PERSONAL_CARE'
  | 'EDUCATION'
  | 'FEES_CHARGES'
  | 'LOAN_PAYMENT'
  | 'TAXES_GOV'
  | 'GIFTS_DONATIONS'
  | 'BUSINESS_SERVICES'
  | 'UNCATEGORIZED'

export type CategorySource = 'rule' | 'pfc' | 'manual' | 'default'
export type TransactionSource = 'plaid' | 'manual'
export type MatchType = 'contains' | 'equals' | 'regex'
export type ItemStatus = 'active' | 'needsReauth' | 'error'

export interface Transaction {
  id: string
  account_id: string
  amount_cents: number // signed: negative = outflow/spending
  currency: string
  date: string // YYYY-MM-DD
  merchant: string
  raw_name: string
  category: Category
  category_source: CategorySource
  pfc_primary: string | null
  pfc_detailed: string | null
  source: TransactionSource
  pending: boolean
  plaid_txn_id: string | null
  receipt_id: string | null
  possible_duplicate_of: string | null
  is_transfer: boolean
  notes: string
  created_at: string
  updated_at: string
}

export interface Account {
  id: string
  plaid_account_id: string | null
  name: string
  mask: string | null
  type: string
  subtype: string | null
  institution_id: string | null
  balance_cents: number
  currency: string
  is_asset: boolean
  is_liability: boolean
  updated_at: string
}

export interface PlaidItem {
  id: string
  institution_id: string | null
  institution_name: string
  status: ItemStatus
  products: string[]
  last_sync_at: string | null
}

export interface Rule {
  id: string
  match_type: MatchType
  pattern: string
  category: Category
  priority: number
  created_at: string
}

export interface SyncResult {
  added: number
  modified: number
  removed: number
  flagged_duplicates: number
}

export type AlertType =
  | 'large_transaction'
  | 'new_merchant'
  | 'foreign_transaction'
  | 'rapid_repeat'
  | 'budget_warning'
  | 'budget_exceeded'
  | 'new_recurring'
  | 'recurring_amount_change'

export type Flow = 'inflow' | 'outflow'

export type Severity = 'info' | 'warning' | 'critical'

export interface Alert {
  id: string
  type: AlertType
  severity: Severity
  title: string
  message: string
  txn_id: string | null
  category: Category | null
  amount_cents: number | null
  read: boolean
  created_at: string
}

export interface Budget {
  month: string // YYYY-MM
  caps_cents: Record<string, number>
  spent_cents: Record<string, number>
  updated_at: string
}

export interface UserSettings {
  large_txn_threshold_cents: number
  budget_warn_percent: number
  home_country: string
  email: string | null
  fcm_tokens: string[]
}

export interface RecurringStream {
  id: string
  merchant: string
  description: string
  category: Category
  frequency: string // WEEKLY|BIWEEKLY|SEMI_MONTHLY|MONTHLY|ANNUALLY|UNKNOWN
  flow: Flow
  average_amount_cents: number // signed
  last_amount_cents: number
  last_date: string | null
  is_active: boolean
  status: string
  updated_at: string
}

export interface UpcomingCashFlow {
  date: string
  merchant: string
  amount_cents: number
  flow: Flow
  category: Category
}

export interface CashFlowForecast {
  horizon_days: number
  current_balance_cents: number
  projected_inflow_cents: number
  projected_outflow_cents: number
  net_cents: number
  projected_end_balance_cents: number
  upcoming: UpcomingCashFlow[]
}
