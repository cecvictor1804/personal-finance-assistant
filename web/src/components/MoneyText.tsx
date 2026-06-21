import { cn } from '@/lib/utils'
import { formatCents } from '@/lib/utils'

interface Props {
  cents: number
  currency?: string
  /** Color positive green / negative red. Off by default (neutral). */
  colorize?: boolean
  className?: string
}

export function MoneyText({ cents, currency = 'USD', colorize = false, className }: Props) {
  const color = colorize ? (cents < 0 ? 'text-red-600' : cents > 0 ? 'text-emerald-600' : '') : ''
  return (
    <span className={cn('tabular-nums', color, className)}>{formatCents(cents, currency)}</span>
  )
}
