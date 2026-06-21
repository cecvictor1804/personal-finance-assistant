---
category: Primitives
---

# Progress

A horizontal progress/meter bar — good for budget usage. `value` is a percent (0–100, clamped).

## Props
- `value: number` — percent complete.
- `barClassName?` — color the filled bar (e.g. `bg-amber-500`, `bg-red-500` for over-budget).
- `className?` — style the track.

## Usage
```tsx
<div className="flex w-72 flex-col gap-4">
  <Progress value={45} />
  <Progress value={82} barClassName="bg-amber-500" />
  <Progress value={100} barClassName="bg-red-500" />
</div>
```

## Notes
- Default bar is `bg-slate-900`. Switch `barClassName` by threshold (e.g. amber ≥80%, red ≥100%).
