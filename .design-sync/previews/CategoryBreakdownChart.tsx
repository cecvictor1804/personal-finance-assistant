import { CategoryBreakdownChart } from 'pfa-web'

const data = [
  { category: 'GROCERIES', label: 'Groceries', value_cents: 84200, color: '#84cc16' },
  { category: 'FOOD_DINING', label: 'Food & Dining', value_cents: 61300, color: '#f97316' },
  { category: 'TRANSPORT', label: 'Transport', value_cents: 38900, color: '#0ea5e9' },
  { category: 'ENTERTAINMENT', label: 'Entertainment', value_cents: 24500, color: '#a855f7' },
  { category: 'SHOPPING', label: 'Shopping', value_cents: 19800, color: '#ec4899' },
]

export function Donut() {
  return (
    <div className="w-[360px]">
      <CategoryBreakdownChart data={data} />
    </div>
  )
}
