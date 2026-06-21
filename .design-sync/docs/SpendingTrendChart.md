---
category: Charts
---

# SpendingTrendChart

A grouped bar chart of monthly spending vs income (Recharts). Renders responsively at 100% width,
260px tall — give it a width-constrained parent.

## Props
- `data: Array<{ month: string; spending_cents: number; income_cents: number }>` — oldest first;
  `month` is a short label like `"Jun 26"`; amounts are positive cents.

## Usage
```tsx
<div className="w-[460px]">
  <SpendingTrendChart data={[
    { month: 'May 26', spending_cents: 231000, income_cents: 355000 },
    { month: 'Jun 26', spending_cents: 252000, income_cents: 320000 },
  ]} />
</div>
```

## Notes
- Income bars are green, spending bars red; legend + axes are built in.
- Wrap in a width-constrained parent — the ResponsiveContainer fills it.
