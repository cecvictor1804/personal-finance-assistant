import { Badge } from '@/components/ui/badge'
import { CATEGORY_COLORS, categoryLabel } from '@/lib/categories'
import type { Category } from '@/types'

export function CategoryBadge({ category }: { category: Category }) {
  const color = CATEGORY_COLORS[category]
  return (
    <Badge style={{ backgroundColor: `${color}1a`, color }}>
      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
      {categoryLabel(category)}
    </Badge>
  )
}
