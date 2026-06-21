---
category: Primitives
---

# Input

A styled text input. Forwards all standard `<input>` attributes and a `ref`.

## Props
- standard `<input>` attributes (`type`, `placeholder`, `value`/`defaultValue`, `onChange`,
  `disabled`, …) + `className`.

## Usage
```tsx
<Input placeholder="Search transactions…" value={q} onChange={(e) => setQ(e.target.value)} />
```

## Notes
- Full-width by default (`w-full`); constrain with a wrapper or `className`.
- Disabled state is styled for you.
