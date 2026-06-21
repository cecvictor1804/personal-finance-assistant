---
category: Primitives
---

# Spinner

An animated loading spinner (lucide `Loader2`). A `CenteredSpinner` helper is also exported for
full-width loading blocks.

## Props
- `Spinner`: `className?` (size/color, e.g. `h-6 w-6 text-slate-400`).
- `CenteredSpinner`: `label?: string` — centered spinner with an optional caption, padded.

## Usage
```tsx
<div className="flex items-center gap-2 text-slate-600">
  <Spinner /> <span className="text-sm">Syncing transactions…</span>
</div>

<CenteredSpinner label="Loading accounts…" />
```

## Notes
- `Spinner` defaults to `h-4 w-4`; resize via `className`.
