// Lean barrel entry for /design-sync (see .design-sync/config.json `--entry`).
// Re-exports ONLY the presentational component set so esbuild bundles those
// (and their transitive deps) without pulling in the app shell — main.tsx's
// createRoot().render(), firebase init, the router, or data hooks.
//
// Lives in web/ (not .design-sync/) so the converter resolves PKG_DIR to
// web/package.json. Kept out of src/ so it isn't part of the app's tsc build.
// `@/` resolves to web/src via tsconfig paths (cfg.tsconfig).
export * from '@/components/ui/button'
export * from '@/components/ui/card'
export * from '@/components/ui/badge'
export * from '@/components/ui/input'
export * from '@/components/ui/select'
export * from '@/components/ui/progress'
export * from '@/components/ui/spinner'
export * from '@/components/MoneyText'
export * from '@/components/CategoryBadge'
export * from '@/components/charts/SpendingTrendChart'
export * from '@/components/charts/CategoryBreakdownChart'
