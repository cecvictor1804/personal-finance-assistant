/**
 * Dedicated Tailwind config for the /design-sync bundle. Scans the synced
 * component sources AND the authored preview files so every utility class they
 * use lands in the compiled stylesheet (web/.ds-styles.css → cfg.cssEntry).
 * Mirrors web/tailwind.config.js (stock theme, no custom tokens). Run from the
 * repo root so the content globs resolve.
 */
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    'web/src/components/**/*.{ts,tsx}',
    'web/src/lib/**/*.{ts,tsx}',
    '.design-sync/previews/**/*.tsx',
  ],
  theme: { extend: {} },
  plugins: [],
}
