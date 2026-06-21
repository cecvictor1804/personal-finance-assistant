# Personal Finance UI — how to build with this library

A small React component set for a personal-finance dashboard (accounts, transactions,
budgets, spending charts). Styling is **stock Tailwind CSS utility classes** — there are no
custom design tokens and **no theme provider or wrapper to mount**. Import a component and
render it; it is styled the moment the bound stylesheet is present.

## Setup
- **No provider needed.** Components are standalone. Do not wrap the app in a ThemeProvider —
  there isn't one.
- The compiled stylesheet ships in `styles.css` (which `@import`s `_ds_bundle.css`). That is the
  whole styling surface — load it and components render correctly.
- Every component takes an optional `className` (merged with the component's own classes via
  `tailwind-merge`, so your class wins on conflicts). Pass Tailwind utilities to extend layout.

## Styling idiom — stock Tailwind, slate-based
Style your own layout with the same Tailwind vocabulary the components use:

| Concern | Classes used in this library |
|---|---|
| Layout | `flex`, `flex-col`, `flex-wrap`, `items-center`, `items-baseline`, `justify-between`, `gap-1`…`gap-4` |
| Spacing | `p-5`, `px-3`, `px-4`, `py-0.5`, `pt-2`, `pb-2` |
| Color (neutral) | `bg-white`, `bg-slate-100`, `text-slate-500`, `text-slate-600`, `text-slate-700`, `text-slate-900`, `border-slate-200`, `border-slate-300` |
| Color (semantic) | `bg-slate-900` (primary), `bg-red-600`/`text-red-600` (danger/outflow), `text-emerald-600` (inflow), amber/emerald tints for status |
| Radius | `rounded-md` (controls), `rounded-xl` (cards), `rounded-full` (badges/pills) |
| Type | `text-xs`, `text-sm`, `text-lg`, `text-2xl`, `font-medium`, `font-semibold`, `tabular-nums` (money) |

**Important:** the bound stylesheet contains only the Tailwind classes the shipped components and
their examples use. When you add layout glue, prefer classes from the table above; an arbitrary
unused Tailwind class may not be present. If you need a class that isn't styled, keep to this
slate-based palette and the spacing/radius scale above so the result stays on-brand.

## Money + categories (domain conventions)
- Monetary amounts are **signed integer cents** — negative = outflow/spending, positive = inflow.
  Render them with `MoneyText` (`<MoneyText cents={-1299} colorize />` → red `-$12.99`); never format
  cents by hand.
- `CategoryBadge` takes a `category` enum (e.g. `"GROCERIES"`, `"INCOME"`) and supplies its own
  color + label — don't restyle it.

## Compounds & extras (in the bundle, no separate card)
- **Card** composes with `CardHeader`, `CardTitle`, `CardContent` (all exported).
- **Spinner** has a `CenteredSpinner({ label })` sibling for full-width loading blocks.

## Where the truth lives
- `styles.css` (+ its `_ds_bundle.css` import) — the exact class set that's actually styled.
- Each component's `<Name>.d.ts` (the prop contract) and `<Name>.prompt.md` (usage) under
  `components/<group>/<Name>/`.

## One idiomatic example — an account balance card
```tsx
import { Card, CardHeader, CardTitle, CardContent, MoneyText } from 'pfa-web'

<div className="w-72">
  <Card>
    <CardHeader>
      <CardTitle>Checking · Chase ····4821</CardTitle>
    </CardHeader>
    <CardContent>
      <MoneyText cents={482310} className="text-2xl font-semibold" />
    </CardContent>
  </Card>
</div>
```
