---
category: Finance
---

# CategoryBadge

A `Badge` preset for a spending category — supplies the category's brand color (dot + tinted
background) and human label automatically.

## Props
- `category` — one of the category enum values: `INCOME`, `TRANSFER`, `FOOD_DINING`, `GROCERIES`,
  `SHOPPING`, `TRANSPORT`, `TRAVEL`, `BILLS_UTILITIES`, `RENT_MORTGAGE`, `HEALTHCARE`,
  `ENTERTAINMENT`, `PERSONAL_CARE`, `EDUCATION`, `FEES_CHARGES`, `LOAN_PAYMENT`, `TAXES_GOV`,
  `GIFTS_DONATIONS`, `BUSINESS_SERVICES`, `UNCATEGORIZED`.

## Usage
```tsx
<div className="flex flex-wrap gap-2">
  <CategoryBadge category="GROCERIES" />
  <CategoryBadge category="INCOME" />
  <CategoryBadge category="RENT_MORTGAGE" />
</div>
```

## Notes
- Color + label are fixed per category — don't restyle. For a custom label, use a plain `Badge`.
