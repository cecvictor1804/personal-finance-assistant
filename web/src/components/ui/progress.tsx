import { cn } from '@/lib/utils'

export function Progress({
  value,
  barClassName,
  className,
}: {
  value: number
  barClassName?: string
  className?: string
}) {
  const pct = Math.min(100, Math.max(0, value))
  return (
    <div className={cn('h-2 w-full overflow-hidden rounded-full bg-slate-100', className)}>
      <div
        className={cn('h-full rounded-full bg-slate-900 transition-all', barClassName)}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}
