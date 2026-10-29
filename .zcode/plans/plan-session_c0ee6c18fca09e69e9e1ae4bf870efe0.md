# UI Overhaul Plan — "Ember" design system, dark-first, full navigation

**Grounding from research:** dark-first + bento grids + subtle glass/liquid-glass surfaces are the dominant 2025–26 AI-SaaS look (Linear/Vercel-style radial glow); Tailwind v4 needs `@theme inline` tokens + `@custom-variant dark` (already present); `next-themes` is installed but never wired; the current palette is default shadcn grayscale — hence "plain". **Locked choices:** ember/fire-orange accent, dark by default with light/dark toggle, auto-roast kept but polished. **No backend changes needed** — analytics computes client-side from existing endpoints.

## Phase 1 — Design foundation + consistent app shell (the consistency fix)
1. Install `framer-motion`; add shadcn `sheet` + `chart` components via CLI.
2. **`globals.css` rewrite — the "Ember" token system**: dark-first warm-tinted surfaces (layered elevation instead of harsh borders), ember primary (`oklch` orange) + ember→amber gradients, full chart palette (ember/amber/teal/violet/rose), light theme = warm paper + same ember, glow/shimmer keyframes.
3. **Theme wiring**: `ThemeProvider` (next-themes, `attribute="class"`, `defaultTheme="dark"`) in root layout + `suppressHydrationWarning`; `ThemeToggle` (sun/moon) component.
4. **AppShell + route group**: move `dashboard, history, analytics, upload, profile, analysis/[id]` under one `(app)` route group whose layout = auth guard + proper flex shell (fixed sidebar + `main`) — kills the top-gap quirk everywhere. Old `dashboard/layout.tsx` absorbed.
5. **New Sidebar**: brand (flame + wordmark), nav = Overview / Roasts (history) / Analytics, big ember **"New roast"** CTA, then Profile, ThemeToggle, user card + logout. Mobile: hamburger → shadcn Sheet. Shared `PageHeader` (title + description + actions) used by every page.

## Phase 2 — Overview (dashboard bento) + Roasts (history)
- `/dashboard` becomes a **bento overview**: stat tiles (roasts count, avg score, best score, resumes), latest roast card with score ring, streak/recent activity, prominent "New roast" tile. Staggered fade-in animations.
- `/history`: full roast list (AnalysisCard restyled: score ring chip, animated status badges) + uploaded resumes in a tab; `AnalysisCard` links stay `/analysis/[id]`.
- Empty states upgraded (ember icon, CTA); toast notifications on actions (sonner, already installed).

## Phase 3 — Upload + roast experience + result (the polish)
- **Upload**: glass dropzone (animated ember dashed border on drag), file chip with size, gradient CTA "Upload & roast". Auto-roast stays — but the transition becomes an animated hand-off (button morph → ember sweep).
- **`/analysis/[id]` progress**: full "roast experience" — animated ember flame loader, stage checklist with per-stage transitions and a moving ember progress bar, pulsing glow card. Feels like a destination, not a teleport.
- **Result**: animated **score ring** (SVG stroke animation counting up), gradient roast card (ember-tinted glass), findings as bento cards with per-item fade-in, category bars animating on load, styled partial banner. Restyles existing `RoastResult`/`StageProgress`.

## Phase 4 — Landing page (Linear-style dark hero)
- Sticky glass navbar; hero with radial ember glow + gradient headline + CTAs; CSS-built product mock (score ring + roast snippet); features bento (4 expert evaluators / hybrid scoring / brutal-but-constructive / private by design); 3-step "how it works"; final CTA + footer. Scroll-reveal animations via framer-motion. Auth pages get matching glass-card treatment.

## Phase 5 — Analytics page (new, your missing page)
- `/analytics`, client-computed from `GET /analyses` + `/resumes`: 4 stat tiles, **score trend** area chart (recharts via shadcn ChartContainer, ember palette), **score distribution** bar chart, recent activity feed, per-mode split. Empty state when no roasts yet.

## Phase 6 — Verification
- `tsc` / eslint / `next build` green; browser walkthrough with screenshots of every page in **both themes** (desktop + one mobile width); fix what looks off; update `PROGRESS.md`. No commits.

**References:** [SaaS design trends 2026](https://toimi.pro/blog/best-saas-website-designs), [Bento grids guide](https://www.saasframe.io/blog/designing-bento-grids-that-actually-work-a-2026-practical-guide), [AI-first SaaS design](https://www.outcrowd.io/blog/2026-design-trends-for-ai-first-saas-products), [Dark theming UX patterns](https://www.saasui.design/blog/saas-dark-mode-theming-ux-patterns), [shadcn dark mode](https://ui.shadcn.com/docs/dark-mode/next), [Tailwind v4 theming](https://ui.shadcn.com/docs/tailwind-v4), [AI startup aesthetic analysis](https://www.setproduct.com/blog/why-every-ai-startup-looks-the-same), [Dark SaaS analytics refs](https://dribbble.com/shots/27428790-Dark-SaaS-Analytics-Dashboard-Revenue-Orders-Conversion).