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
  // Curated on-brand palette emitted regardless of content scanning, so the
  // claude.ai/design agent's own layout glue (not just the shipped components'
  // classes) renders styled. Slate neutrals + semantic (emerald/green income,
  // red outflow/danger, amber warning) + a few finance accents. No hover:/focus:
  // variants (they multiply size) — add later if needed.
  safelist: [
    // layout / display (non-parametric)
    'flex', 'inline-flex', 'grid', 'flex-col', 'flex-row', 'flex-wrap', 'flex-1',
    'hidden', 'block', 'inline-block', 'relative', 'absolute', 'overflow-hidden',
    'truncate', 'tabular-nums', 'whitespace-nowrap',
    'items-center', 'items-start', 'items-end', 'items-baseline',
    'justify-center', 'justify-between', 'justify-start', 'justify-end',
    'text-left', 'text-center', 'text-right', 'mx-auto', 'min-w-0',
    'border', 'border-t', 'border-b', 'divide-y',
    // scales (patterns)
    { pattern: /^gap-(0|1|2|3|4|5|6|8)$/ },
    { pattern: /^(p|px|py|pt|pb|pl|pr)-(0|1|2|3|4|5|6|8|10|12)$/ },
    { pattern: /^(m|mx|my|mt|mb)-(0|1|2|3|4|6|auto)$/ },
    { pattern: /^(w|h)-(2|3|4|5|6|8|10|12|16|24|32|full|auto)$/ },
    { pattern: /^max-w-(xs|sm|md|lg|xl|2xl|full)$/ },
    { pattern: /^grid-cols-(1|2|3|4|6|12)$/ },
    { pattern: /^col-span-(1|2|3|4|6|12)$/ },
    { pattern: /^rounded(-(sm|md|lg|xl|2xl|full))?$/ },
    { pattern: /^shadow(-(sm|md|lg))?$/ },
    { pattern: /^text-(xs|sm|base|lg|xl|2xl|3xl)$/ },
    { pattern: /^font-(normal|medium|semibold|bold)$/ },
    // color: neutrals (full slate scale) + white
    { pattern: /^(bg|text|border)-slate-(50|100|200|300|400|500|600|700|800|900)$/ },
    { pattern: /^(bg|text|border)-white$/ },
    // color: semantic (income / outflow / warning)
    { pattern: /^(bg|text|border)-(emerald|green|red|amber)-(50|100|200|500|600|700)$/ },
    // color: finance category accents
    { pattern: /^(bg|text)-(sky|lime|orange|pink|indigo|violet|teal)-(100|500|600)$/ },
  ],
  theme: { extend: {} },
  plugins: [],
}
