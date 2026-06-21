import { Select } from 'pfa-web'

export function CategoryFilter() {
  return (
    <div className="w-60">
      <Select defaultValue="GROCERIES">
        <option value="ALL">All categories</option>
        <option value="GROCERIES">Groceries</option>
        <option value="FOOD_DINING">Food &amp; Dining</option>
        <option value="TRANSPORT">Transport</option>
        <option value="INCOME">Income</option>
      </Select>
    </div>
  )
}
