import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TrendDatum } from '@/lib/selectors'
import { formatCents } from '@/lib/utils'

function compact(cents: number): string {
  const dollars = cents / 100
  if (Math.abs(dollars) >= 1000) return `$${(dollars / 1000).toFixed(1)}k`
  return `$${dollars.toFixed(0)}`
}

export function SpendingTrendChart({ data }: { data: TrendDatum[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
        <XAxis dataKey="month" tickLine={false} axisLine={false} fontSize={12} stroke="#94a3b8" />
        <YAxis tickFormatter={compact} tickLine={false} axisLine={false} fontSize={12} stroke="#94a3b8" width={48} />
        <Tooltip
          formatter={(v: number, name) => [formatCents(v), name === 'spending_cents' ? 'Spending' : 'Income']}
          cursor={{ fill: '#f1f5f9' }}
        />
        <Legend
          formatter={(v) => (v === 'spending_cents' ? 'Spending' : 'Income')}
          iconType="circle"
          wrapperStyle={{ fontSize: 12 }}
        />
        <Bar dataKey="income_cents" fill="#16a34a" radius={[4, 4, 0, 0]} />
        <Bar dataKey="spending_cents" fill="#ef4444" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
