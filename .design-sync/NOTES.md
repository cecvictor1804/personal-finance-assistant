# design-sync notes — Personal Finance UI

## What this syncs
`web/` is a Vite **application** (`pfa-web`, private), NOT a packaged design system.
There is no Storybook and no library build. We sync the presentational component subset
(11 components) via the **package shape** using a hand-written barrel entry.

Scoped components (11): Button, Card, Badge, Input, Select, Progress, Spinner, MoneyText,
CategoryBadge, SpendingTrendChart, CategoryBreakdownChart. Excluded app glue: Layout,
ProtectedRoute (pull in router/auth/firebase/data hooks).

Bundle also exports subcomponents with no standalone card/contract: **CardHeader, CardTitle,
CardContent** (compose inside Card) and **CenteredSpinner** (full-width loading). Documented
in conventions.md + the Card/Spinner contracts.

## Key sync inputs (committed, durable)
- `web/ds-entry.tsx` — barrel entry (`--entry`). MUST live in `web/` so the converter resolves
  PKG_DIR → `web/package.json`. `@/` resolves to `web/src` via `cfg.tsconfig`.
- `.design-sync/tailwind.ds.config.cjs` + `.design-sync/ds-input.css` — Tailwind compile inputs. The
  config carries a curated `safelist` palette (slate neutrals + emerald/green/red/amber semantics +
  finance accents + layout/spacing/type scales) so the design agent's own layout glue renders styled,
  not just the classes the shipped components use. No `hover:`/`focus:` variants (size).
- `.design-sync/config.json` — `cfg.dtsPropsFor` hand-writes every contract (no built `.d.ts`
  exists, so ts-morph finds no props). Update dtsPropsFor if a component's source props change.
  `cfg.docsDir` points at `../.design-sync/docs`.
- `.design-sync/previews/*.tsx` — authored previews (one per component).
- `.design-sync/docs/*.md` — per-component docs; frontmatter `category` sets the DS-pane group
  (Primitives / Finance / Charts — only overrides `general`/`misc`, so charts stay `charts`), body
  becomes `<Name>.prompt.md`. Bound via `cfg.docsDir`.
- `.design-sync/conventions.md` — README header (wired via `readmeHeader`).

## Build/verify commands (run from repo root)
1. Regenerate CSS (REQUIRED before every build — scans `previews/` for utility classes):
   `node web/node_modules/tailwindcss/lib/cli.js -c .design-sync/tailwind.ds.config.cjs -i .design-sync/ds-input.css -o web/.ds-styles.css`
2. Build: `node .ds-sync/package-build.mjs --config .design-sync/config.json --node-modules web/node_modules --entry web/ds-entry.tsx --out ./ds-bundle`
3. Validate: `node .ds-sync/package-validate.mjs ./ds-bundle`
4. Capture: `node .ds-sync/package-capture.mjs --out ./ds-bundle [--force]`
- Driver (conventions rebuild / re-sync): `node .ds-sync/resync.mjs --config .design-sync/config.json --node-modules web/node_modules --entry web/ds-entry.tsx --out ./ds-bundle [--remote .design-sync/.cache/remote-sync.json]` (first sync omits `--remote`).

## CSS strategy (stock Tailwind — no custom tokens)
`web/tailwind.config.js` has an empty `theme.extend`; the design language is stock Tailwind
+ shadcn-style component variants. The compiled stylesheet (`web/.ds-styles.css`, gitignored,
cfg.cssEntry) is appended into `_ds_bundle.css` and reaches designs via the `styles.css` closure.
It contains classes used by the components + previews PLUS the curated `safelist` palette in
`tailwind.ds.config.cjs` — so the agent has a broad on-brand vocabulary. Classes far outside the
safelist (exotic colors/shades, rare utilities) still won't be present. (Documented in conventions.md.)

## Known render warns (triaged, expected)
- `tokens: 56 defined, 13 referenced (1 missing, below threshold)` — non-blocking; a recharts/
  tailwind internal var. Safe to ignore.

## Re-sync risks / watch-list
- `web/.ds-styles.css` is GENERATED + gitignored — re-run step 1 before any build or components/
  previews lose their utility classes (renders unstyled).
- **Capture animation settle**: recharts charts (`ResponsiveContainer` async measure + `Pie`
  entrance animation) capture COLLAPSED in a one-shot screenshot. The staged
  `.ds-sync/package-capture.mjs` `settle()` was patched with `await page.waitForTimeout(1800)`.
  `.ds-sync/` is gitignored and re-copied on re-sync — **re-apply this patch after the `cp -r`
  step**, or the chart cells will collapse and re-grade as needs-work. (The shipped bundle and the
  live claude.ai/design app render the charts fine; this only affects the static capture.)
- `cfg.dtsPropsFor` is hand-maintained — drifts if component source props change.
- Playwright + typescript were installed into `.ds-sync/node_modules` (gitignored) — reinstall on
  a fresh clone for the render + .d.ts-parse checks.
