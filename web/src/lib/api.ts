// Typed REST client for the FastAPI backend. Attaches the Firebase ID token as a bearer token
// when a user is signed in (the backend may also run with AUTH_DISABLED locally).

import { auth } from './firebase'
import type {
  Account,
  Alert,
  Budget,
  CashFlowForecast,
  Category,
  MatchType,
  PlaidItem,
  Receipt,
  RecurringStream,
  Rule,
  SyncResult,
  Transaction,
  UserSettings,
} from '@/types'

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function authHeaders(): Promise<Record<string, string>> {
  const user = auth?.currentUser
  if (!user) return {}
  const token = await user.getIdToken()
  return { Authorization: `Bearer ${token}` }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(await authHeaders()),
      ...(init?.headers ?? {}),
    },
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}${body ? `: ${body}` : ''}`)
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export interface TransactionFilters {
  limit?: number
  start_date?: string
  end_date?: string
  category?: string
  account_id?: string
}

function qs(params: Record<string, string | number | undefined>): string {
  const sp = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '') sp.set(k, String(v))
  }
  const s = sp.toString()
  return s ? `?${s}` : ''
}

export const api = {
  listTransactions: (f: TransactionFilters = {}) =>
    request<Transaction[]>(`/transactions${qs({ ...f })}`),

  getTransaction: (id: string) => request<Transaction>(`/transactions/${id}`),

  createManualTransaction: (body: {
    account_id: string
    amount_cents: number
    date: string
    merchant?: string
    category?: Category
    notes?: string
  }) =>
    request<Transaction>('/transactions', { method: 'POST', body: JSON.stringify(body) }),

  recategorize: (id: string, category: Category, remember = true) =>
    request<Transaction>(`/transactions/${id}/recategorize`, {
      method: 'POST',
      body: JSON.stringify({ category, remember }),
    }),

  listAccounts: () => request<Account[]>('/accounts'),

  listItems: () => request<PlaidItem[]>('/items'),

  syncNow: () => request<SyncResult>('/items/sync', { method: 'POST' }),

  reauthLinkToken: (itemId: string) =>
    request<{ link_token: string }>(`/items/${itemId}/reauth-link-token`, { method: 'POST' }),

  listRules: () => request<Rule[]>('/rules'),

  createRule: (body: { match_type: MatchType; pattern: string; category: Category; priority?: number }) =>
    request<Rule>('/rules', { method: 'POST', body: JSON.stringify(body) }),

  deleteRule: (id: string) =>
    request<{ message: string }>(`/rules/${id}`, { method: 'DELETE' }),

  getBudget: (month: string) => request<Budget>(`/budgets/${month}`),

  setBudgetCaps: (month: string, caps_cents: Record<string, number>) =>
    request<Budget>(`/budgets/${month}`, {
      method: 'PUT',
      body: JSON.stringify({ caps_cents }),
    }),

  listAlerts: (unreadOnly = false) =>
    request<Alert[]>(`/alerts${unreadOnly ? '?unread_only=true' : ''}`),

  markAlertRead: (id: string) =>
    request<{ message: string }>(`/alerts/${id}/read`, { method: 'POST' }),

  getSettings: () => request<UserSettings>('/settings'),

  updateSettings: (settings: UserSettings) =>
    request<UserSettings>('/settings', { method: 'PUT', body: JSON.stringify(settings) }),

  registerFcmToken: (token: string) =>
    request<UserSettings>('/settings/fcm-token', {
      method: 'POST',
      body: JSON.stringify({ token }),
    }),

  listRecurring: () => request<RecurringStream[]>('/recurring'),

  refreshRecurring: () =>
    request<SyncResult>('/recurring/refresh', { method: 'POST' }),

  getForecast: (horizonDays = 30) =>
    request<CashFlowForecast>(`/forecast?horizon_days=${horizonDays}`),

  listReceipts: () => request<Receipt[]>('/receipts'),

  attachReceipt: (receiptId: string, txnId: string) =>
    request<Receipt>(`/receipts/${receiptId}/attach`, {
      method: 'POST',
      body: JSON.stringify({ txn_id: txnId }),
    }),
}
