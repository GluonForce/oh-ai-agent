# Design — OH AI Agent

A locked design system for this app. Every page redesign reads this file before
emitting code. Do not regenerate per page — extend or amend this file when the
system needs to grow.

## Genre
modern-minimal

## Mood
utilitarian — instrument-panel clarity for UK occupational health professionals.
Function over flourish. One cobalt signal. Cool engineered paper.

## Macrostructure family
- Marketing pages: none (app-only product)
- App pages: Workbench — sidebar shell, form→results flow, hairline cards, tables
- Dashboard / overview: Stat-Led — asymmetric metric band (dominant status + secondary counts)
- Content / log pages: Workbench-data — full-width tables, mono IDs, dense rows

Pages within a family share shape; they vary only on allowed knobs (phase badge, result tabs).

## Theme
Cool Cobalt (catalog Cobalt, tuned for app chrome — no marketing code-hero).

- `--color-paper`   oklch(98.5% 0.004 250)
- `--color-paper-2` oklch(97% 0.006 250)
- `--color-ink`     oklch(24% 0.02 258)
- `--color-ink-2`   oklch(34% 0.018 257)
- `--color-rule`    oklch(90% 0.01 250)
- `--color-accent`  oklch(58% 0.20 256)
- `--color-focus`   oklch(58% 0.20 256)

Semantic status (compliance / priority / audit events):

- `--color-success` oklch(55% 0.14 150)
- `--color-warning` oklch(70% 0.14 75)
- `--color-danger`  oklch(55% 0.18 25)
- `--color-info`    oklch(55% 0.12 250)
- `--color-neutral` oklch(55% 0.02 258)

## Typography
- Display: Space Grotesk, weight 600, style normal, tracking -0.02em
- Body:    Inter, weight 400/500
- Mono:    JetBrains Mono, weight 400/500
- Type scale anchor: page title ≈ 1.5rem (display); dashboard status figure ≈ 2rem

## Spacing
4-point named scale in `frontend/src/app/globals.css`. Prefer Tailwind space utilities mapped from the theme. Main content padding `--space-md` (1.5rem).

## Motion
- Easings: `--ease-out: cubic-bezier(0.16, 1, 0.3, 1)`
- Reveal: none on app pages
- Reduced-motion: opacity-only / animation none, ≤ 150 ms

## Microinteractions stance
- Silent or toast success (sonner) — no celebratory confetti
- Hover delay 800 ms on tooltips · focus delay 0 ms
- Spinners only while awaiting LLM; prefer Progress when wait > 2s (future)

## CTA voice
- Primary CTA: solid cobalt fill, 6px radius, short verb labels ("Generate", "Run audit")
- Secondary CTA: hairline outline on paper, same radius

## Nav
- N3 side-rail (desktop) + mobile sheet
- Active row: cobalt fill + light ink
- Phase tags: mono uppercase, muted on inactive; `primary-foreground/70` on active

## Per-page allowances
- App pages MUST NOT use enrichment
- No side-stripe callouts — use `Callout` (hairline + accent tick)
- Status colours only via semantic Badge variants / `statusStyles`
- Dashboard MAY use asymmetric Stat-Led band; form pages keep `max-w-5xl`

## What pages MUST share
- Wordmark "OH AI Agent" + Shield
- Cobalt accent ≤ 5% of viewport
- Space Grotesk display + Inter body + JetBrains Mono
- CTA voice and radius
- Sidebar PDCA IA

## What pages MAY differ on
- Presence of phase Badge (CHECK / REVIEW / ACT)
- Results tabs (Workflows only)
- Content width (form `max-w-5xl` vs full-bleed tables)

## Exports

### tokens.css (canonical — mirrored in globals.css `:root`)
```css
:root {
  --color-paper: oklch(98.5% 0.004 250);
  --color-paper-2: oklch(97% 0.006 250);
  --color-ink: oklch(24% 0.02 258);
  --color-ink-2: oklch(34% 0.018 257);
  --color-rule: oklch(90% 0.01 250);
  --color-accent: oklch(58% 0.20 256);
  --color-accent-ink: oklch(99% 0.01 250);
  --color-focus: oklch(58% 0.20 256);
  --color-success: oklch(55% 0.14 150);
  --color-warning: oklch(70% 0.14 75);
  --color-danger: oklch(55% 0.18 25);
  --color-info: oklch(55% 0.12 250);
  --font-display: "Space Grotesk", ui-sans-serif, system-ui, sans-serif;
  --font-body: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
  --space-sm: 1rem;
  --space-md: 1.5rem;
  --space-lg: 2rem;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --dur-short: 220ms;
  --radius-card: 10px;
  --radius-control: 6px;
}
```

### shadcn/ui mapping
- `--background` ← paper
- `--foreground` ← ink
- `--primary` ← accent (cobalt)
- `--primary-foreground` ← accent-ink
- `--muted` ← paper-2
- `--border` / `--input` ← rule
- `--ring` ← focus
- `--radius` ← 0.375rem (6px control base)
