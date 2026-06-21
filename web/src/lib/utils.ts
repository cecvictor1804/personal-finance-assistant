import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Format signed integer cents as a money string, e.g. -1234 -> "-$12.34". */
export function formatCents(cents: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(cents / 100)
}

/** Absolute money (no sign), for spending magnitudes. */
export function formatAbsCents(cents: number, currency = 'USD'): string {
  return formatCents(Math.abs(cents), currency)
}

export function formatDate(iso: string): string {
  const d = new Date(iso.length <= 10 ? `${iso}T00:00:00` : iso)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/** "2026-06" for a date string or Date. */
export function monthKey(d: string | Date): string {
  const date = typeof d === 'string' ? new Date(`${d.slice(0, 10)}T00:00:00`) : d
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}

export function monthLabel(key: string): string {
  const [y, m] = key.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
}

export function currentMonthKey(): string {
  return monthKey(new Date())
}
