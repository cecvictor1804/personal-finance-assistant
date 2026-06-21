import { CategoryBadge } from 'pfa-web'

export function Categories() {
  return (
    <div className="flex flex-wrap gap-2">
      <CategoryBadge category="GROCERIES" />
      <CategoryBadge category="FOOD_DINING" />
      <CategoryBadge category="TRANSPORT" />
      <CategoryBadge category="INCOME" />
      <CategoryBadge category="RENT_MORTGAGE" />
      <CategoryBadge category="ENTERTAINMENT" />
    </div>
  )
}
