import { SpendingTrendChart } from 'pfa-web'

const data = [
  { month: 'Jan 26', spending_cents: 210000, income_cents: 320000 },
  { month: 'Feb 26', spending_cents: 245000, income_cents: 320000 },
  { month: 'Mar 26', spending_cents: 198000, income_cents: 340000 },
  { month: 'Apr 26', spending_cents: 268000, income_cents: 320000 },
  { month: 'May 26', spending_cents: 231000, income_cents: 355000 },
  { month: 'Jun 26', spending_cents: 252000, income_cents: 320000 },
]

export function SixMonths() {
  return (
    <div className="w-[460px]">
      <SpendingTrendChart data={data} />
    </div>
  )
}
