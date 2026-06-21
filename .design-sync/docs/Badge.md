---
category: Primitives
---

# Badge

A small rounded pill for inline status/labels. Styled only as a shape by default — apply a
background + text color via `className`.

## Props
- standard `<span>` attributes + `className`, `style`.

## Usage
```tsx
<div className="flex gap-2">
  <Badge className="bg-emerald-100 text-emerald-700">Posted</Badge>
  <Badge className="bg-amber-100 text-amber-700">Pending</Badge>
  <Badge className="bg-red-100 text-red-700">Possible duplicate</Badge>
</div>
```

## Notes
- For spending-category labels, prefer `CategoryBadge` — it supplies color + label for you.
