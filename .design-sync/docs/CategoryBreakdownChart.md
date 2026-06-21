---
category: Charts
---

# CategoryBreakdownChart

A donut chart of spending by category for one month (Recharts). 100% width, 260px tall — give it a
width-constrained parent. An empty `data` array renders a "No spending this month yet." placeholder.

## Props
- `data: Array<{ category: string; label: string; value_cents: number; color: string }>` — `label`
  shows in the tooltip; `value_cents` is positive cents; `color` is a hex slice color.

## Usage
```tsx
<div className="w-[360px]">
  <CategoryBreakdownChart data={[
    { category: 'GROCERIES', label: 'Groceries', value_cents: 84200, color: '#84cc16' },
    { category: 'FOOD_DINING', label: 'Food & Dining', value_cents: 61300, color: '#f97316' },
  ]} />
</div>
```

## Notes
- Pair slice colors with the app's stable per-category palette (`CATEGORY_COLORS`).
