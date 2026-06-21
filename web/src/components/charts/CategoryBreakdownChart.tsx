import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { CategoryDatum } from '@/lib/selectors'
import { formatCents } from '@/lib/utils'

export function CategoryBreakdownChart({ data }: { data: CategoryDatum[] }) {
  if (data.length === 0) {
    return <div className="py-12 text-center text-sm text-slate-400">No spending this month yet.</div>
  }
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value_cents"
          nameKey="label"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
        >
          {data.map((d) => (
            <Cell key={d.category} fill={d.color} />
          ))}
        </Pie>
        <Tooltip formatter={(v: number, _n, p) => [formatCents(v), p.payload.label]} />
      </PieChart>
    </ResponsiveContainer>
  )
}
