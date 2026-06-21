---
category: Finance
---

# MoneyText

Renders a money amount from **signed integer cents** (the app's money convention: negative =
outflow/spending, positive = inflow/income). Formats via `Intl.NumberFormat`.

## Props
- `cents: number` — signed minor units (e.g. `-1299` → `-$12.99`).
- `currency?: string` — ISO 4217 code, default `"USD"`.
- `colorize?: boolean` — when true, positive renders green, negative red, zero neutral. Default false.
- `className?`.

## Usage
```tsx
<MoneyText cents={482310} className="text-2xl font-semibold" />
<MoneyText cents={-12999} colorize />
```

## Notes
- Always pass integer **cents**, never dollars — `4823.10` would render `$48.23`.
- Uses `tabular-nums` so columns of figures align.
