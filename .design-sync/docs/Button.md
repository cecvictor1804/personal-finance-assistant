---
category: Primitives
---

# Button

The primary action control. Four visual variants and three sizes; forwards all standard
`<button>` attributes (`onClick`, `disabled`, `type`, …) and a `ref`.

## Props
- `variant?: "default" | "outline" | "ghost" | "destructive"` — `default` is the dark primary
  button; `outline` for secondary, `ghost` for low-emphasis, `destructive` for dangerous actions.
- `size?: "sm" | "md" | "icon"` — `md` default; `icon` is a square button for a single glyph.
- `className?` — extra Tailwind classes (merged via tailwind-merge, so yours win on conflicts).

## Usage
```tsx
<div className="flex gap-3">
  <Button onClick={addTxn}>Add transaction</Button>
  <Button variant="outline">Export CSV</Button>
  <Button variant="destructive">Remove account</Button>
</div>
```

## Notes
- Disabled state is handled for you (dims + blocks pointer events).
- Use `size="icon"` with an `aria-label` for icon-only buttons.
