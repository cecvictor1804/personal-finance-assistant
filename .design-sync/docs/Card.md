---
category: Primitives
---

# Card

A bordered, rounded surface for grouping content. Compose it with the exported subcomponents
`CardHeader`, `CardTitle`, and `CardContent`.

## Props
- `Card`, `CardHeader`, `CardContent`: standard `<div>` attributes + `className`.
- `CardTitle`: standard `<h3>` attributes; renders as a small muted label.

## Usage
```tsx
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

## Notes
- `CardTitle` is intentionally a quiet label (`text-sm text-slate-500`) — put the headline value in
  `CardContent`.
- Card is full-width; set a width on a wrapper (`<div className="w-72">`).
