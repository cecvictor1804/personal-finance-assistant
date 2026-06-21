// React Query hooks over the REST client. Reads poll lightly for freshness; Phase 3 will swap the
// reads to Firestore real-time listeners (and add rollups/alerts).

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type TransactionFilters } from '@/lib/api'
import type { Category, MatchType } from '@/types'

const keys = {
  transactions: (f: TransactionFilters) => ['transactions', f] as const,
  accounts: ['accounts'] as const,
  items: ['items'] as const,
  rules: ['rules'] as const,
  budget: (month: string) => ['budget', month] as const,
  alerts: (unread: boolean) => ['alerts', unread] as const,
  settings: ['settings'] as const,
  recurring: ['recurring'] as const,
  forecast: (horizon: number) => ['forecast', horizon] as const,
  receipts: ['receipts'] as const,
}

const LIVE = { refetchInterval: 60_000, staleTime: 30_000 }

export function useTransactions(filters: TransactionFilters = {}) {
  return useQuery({
    queryKey: keys.transactions(filters),
    queryFn: () => api.listTransactions(filters),
    ...LIVE,
  })
}

export function useAccounts() {
  return useQuery({ queryKey: keys.accounts, queryFn: api.listAccounts, ...LIVE })
}

export function useItems() {
  return useQuery({ queryKey: keys.items, queryFn: api.listItems, ...LIVE })
}

export function useRules() {
  return useQuery({ queryKey: keys.rules, queryFn: api.listRules })
}

export function useSyncNow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.syncNow,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      qc.invalidateQueries({ queryKey: keys.accounts })
      qc.invalidateQueries({ queryKey: keys.items })
    },
  })
}

export function useRecategorize() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, category, remember }: { id: string; category: Category; remember?: boolean }) =>
      api.recategorize(id, category, remember ?? true),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      qc.invalidateQueries({ queryKey: keys.rules })
    },
  })
}

export function useCreateManualTransaction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.createManualTransaction,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['transactions'] }),
  })
}

export function useCreateRule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { match_type: MatchType; pattern: string; category: Category; priority?: number }) =>
      api.createRule(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.rules }),
  })
}

export function useDeleteRule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.deleteRule(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.rules }),
  })
}

export function useBudget(month: string) {
  return useQuery({ queryKey: keys.budget(month), queryFn: () => api.getBudget(month), ...LIVE })
}

export function useSetBudgetCaps(month: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (caps: Record<string, number>) => api.setBudgetCaps(month, caps),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.budget(month) })
      qc.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}

export function useAlerts(unreadOnly = false) {
  return useQuery({
    queryKey: keys.alerts(unreadOnly),
    queryFn: () => api.listAlerts(unreadOnly),
    ...LIVE,
  })
}

export function useMarkAlertRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.markAlertRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  })
}

export function useSettings() {
  return useQuery({ queryKey: keys.settings, queryFn: api.getSettings })
}

export function useUpdateSettings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.updateSettings,
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.settings }),
  })
}

export function useRecurring() {
  return useQuery({ queryKey: keys.recurring, queryFn: api.listRecurring, ...LIVE })
}

export function useForecast(horizonDays: number) {
  return useQuery({
    queryKey: keys.forecast(horizonDays),
    queryFn: () => api.getForecast(horizonDays),
    ...LIVE,
  })
}

export function useRefreshRecurring() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.refreshRecurring,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.recurring })
      qc.invalidateQueries({ queryKey: ['forecast'] })
      qc.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}

export function useReceipts() {
  return useQuery({ queryKey: keys.receipts, queryFn: api.listReceipts, ...LIVE })
}

export function useAttachReceipt() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ receiptId, txnId }: { receiptId: string; txnId: string }) =>
      api.attachReceipt(receiptId, txnId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.receipts })
      qc.invalidateQueries({ queryKey: ['transactions'] })
    },
  })
}
