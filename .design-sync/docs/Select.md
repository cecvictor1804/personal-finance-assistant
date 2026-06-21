---
category: Primitives
---

# Select

A styled native `<select>`. Pass `<option>` elements as children. Forwards all standard
`<select>` attributes and a `ref`.

## Props
- standard `<select>` attributes (`value`/`defaultValue`, `onChange`, `disabled`, …) + `className`.

## Usage
```tsx
<Select value={category} onChange={(e) => setCategory(e.target.value)}>
  <option value="ALL">All categories</option>
  <option value="GROCERIES">Groceries</option>
  <option value="TRANSPORT">Transport</option>
</Select>
```

## Notes
- Native select — keyboard navigation and accessibility come for free.
