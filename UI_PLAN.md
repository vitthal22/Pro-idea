# UI Improvement Plan — spacing, density, shell

**Status:** **implemented 2026-11-04** (phases 0–4). Measured results and the
three deviations from the original targets are in section 9.
**Audited:** 2026-11-04, live app at 1440 × 1000, dark theme, real data
(`demo@airoast.dev`: 14 analyses, 18 resumes).
**Scope:** every page, the app shell, and the sidebar. Colour/type direction is a
separate brand pass and is deliberately excluded here.

---

## 1. What is actually wrong

Five causes, all measured, not guessed.

**1. One container for every page.**
The shell gives every route `max-w-6xl` → **1088 px of content width**
(1152 − 2 × 32 padding). That is right for dashboards and wrong for everything
else: a 6-field upload form is 1088 px wide, the roast prose runs 1024 px at
14 px (≈120 characters per line), and the profile card is 1088 px wide for three
centred facts.

**2. Padding compounds instead of adding up to a rhythm.**
`main p-8` (32) → card `p-6 sm:p-8` (32) → nested card `p-4` (16) → inner box
`p-3` (12) puts body text **80–92 px** from the panel edge. The spacing values in
use are 4/12/16/20/24/28/32/40/56/64/80/96/112 — effectively every step, so
nothing groups.

**3. Lists are built from the airy card, not from a list primitive.**
Every roast is a `Card` with 16 px top + 16 px bottom padding around a 44 px text
block → **86 px per row** and 12 px between rows. Fourteen rows = 1468 px. The
card component already ships a `size="sm"` variant (12 px) that no page uses.

**4. Two pages are mostly empty canvas.**
Upload ends at **y = 562** in a 1000 px viewport → **438 px of dead space**.
Profile ends at **y = 506** → **494 px dead**. Both are consequences of (1): the
content is stretched horizontally and never fills vertically.

**5. The shell cannot be collapsed, and its header is heavy.**
The desktop sidebar is a permanent 256 px column with no state anywhere to
remember a preference. The page header is also fixed at 32 px bottom margin,
so content always starts at **120 px** (32 main + 56 header + 32 margin).

Measured page heights at 1440 × 1000: landing **2399**, dashboard **1321**,
history **1588**, analytics **1000** (content ends 934), upload **1000**
(content ends 562), profile **1000** (content ends 506), result **6076**.

---

## 2. The system this plan installs

Three decisions that every page then follows. Everything else is a consequence.

### 2.1 Three content widths inside one constant outer frame

The outer frame never changes, so edges still do not jump between routes (the
earlier fix is preserved). The *inner* column is chosen by content type:

| Variant | Width | Used by | Why |
|---|---|---|---|
| `wide` | 1152 (current `max-w-6xl`) | dashboard, history, analytics | tables and charts earn the width |
| `prose` | 720 (`max-w-3xl`) | result page text blocks | 68–75 characters at 15–16 px |
| `form` | 672 (`max-w-2xl`) | upload, profile, auth | one column of fields, no dead right side |

Rule: a page may narrow its content, never move its outer edge.

### 2.2 One spacing scale

`4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 80` — and nothing else.

| Role | Value |
|---|---|
| Inside a control / chip | 4–8 |
| Card padding (data) | 16 |
| Card padding (reading) | 24 |
| Gap between cards in a group | 12 |
| Gap between groups | 16 |
| Gap between sections | 24 |
| Page header → content | 16 |
| Marketing section gap | 80 |

### 2.3 Three radii, three densities

Radius: **4** (chips, inputs inner), **8** (buttons, inputs), **12** (cards).
Today the app mixes 12, 16.8 and 21.6 px between stacked sections.

Density: `comfortable` (current) and `compact` (lists). Compact = 56 px rows,
`divide-y` instead of gaps, 40 px score rings. Persisted per user, desktop only.

---

## 3. Page-by-page plan

Priority: **P0** = the complaint the user can see today, **P1** = structural,
**P2** = polish. Estimates are arithmetic on the current markup, not measured
after the change.

### 3.1 App shell — every authenticated page

| # | Area | Now | Problem | Change | P |
|---|---|---|---|---|---|
| S1 | Sidebar width | `w-64` (256 px), no toggle, no stored state | Cannot be closed or reopened; 184 px can never be reclaimed | Two-state rail **256 ↔ 72 px**, toggle in the shell, persisted | P0 |
| S2 | Sidebar persistence | none (`navOpen` is local sheet state) | A collapsed state would reset on every navigation | New `ui-store.ts` (`zustand` + `persist`), key `ui-preferences`, `{ collapsed }`; kept out of `auth-storage` so logout does not wipe it | P0 |
| S3 | Hydration | layout is `"use client"`, `useMounted()` already exists | Reading localStorage during render → React 19 mismatch + 184 px snap | `collapsed = mounted && storedCollapsed`; expanded on server/first paint; `transition-none` until mounted | P0 |
| S4 | Content top | `p-8` + 56 px header + `mb-8` = **120 px** to first card | Header looks detached and pushed down | `md:py-5` (20) + header `mb-4` (16) → **first content ≈ 92 px** | P0 |
| S5 | Breakpoint | `md:` for sidebar + `md:p-8` | At 768 px the content drops to 448 px while at 767 it is 735 px — content shrinks 287 px when the screen grows | Move the shell to `lg:`; 768–1023 keeps the mobile header + Sheet | P1 |
| S6 | Sidebar empty gap | `flex h-full flex-col gap-6`, footer `mt-auto` | ~495 px of dead column at 900 px tall; uniform 24 px gap flattens brand/nav/CTA | Group with `gap-3` inside groups, 24 between; footer stays `mt-auto` | P1 |
| S7 | Sidebar nav | 3 links + CTA + Profile in a second unnamed `<nav>`; CTA is 32 px tall vs 36 px links | CTA reads secondary; two landmarks, no accessible names; active state is colour-only | One `<nav aria-label="Main">`, CTA at default height, `aria-current="page"` | P1 |
| S8 | Sidebar overflow | `sticky top-0 h-screen`, no `overflow` | At <420 px viewport height the footer is clipped and unreachable | `md:h-svh md:overflow-y-auto` + `min-h-0` | P1 |
| S9 | Sidebar seam | `bg-sidebar` **and** `border-r border-sidebar-border` | Two separation mechanisms; `--sidebar-border` (8%) ≠ `--border` (9%) in dark | Keep the border, drop the surface step (or make the tokens equal) | P2 |
| S10 | Mobile sheet | `w-72 p-0`, default close button | `data-[side=left]:w-3/4` beats `w-72` → 75vw not 288 px; close button sits over the brand; no `SheetDescription` | `showCloseButton={false}` (nav closes on tap), explicit width class, add `sr-only` description | P2 |
| S11 | Keyboard | no skip link; `<main>` has no id | Every route tabs through ~6 sidebar stops first | Skip link to `#main-content`, `<main id tabIndex={-1}>`, toggle gets `aria-expanded`/`aria-controls` | P2 |
| S12 | Loading header | dashboard/analytics early-return skeletons **without** `PageHeader`; history renders it | Content jumps 32 px and the title swaps a 40 px bar for a 32 px line when data lands | Render `PageHeader` outside the loading branch on every page | P1 |

**Sidebar collapse — smallest correct implementation**

- State: one new store `frontend/src/stores/ui-store.ts` → `{ collapsed, toggle }`.
- Consumer: `(app)/layout.tsx` only. `Sidebar.tsx` reads the ancestor via
  `group-data-[collapsed=true]/sidebar:` variants — no prop drilling, no second
  subscription, mobile Sheet unaffected.
- Widths: `w-64` expanded, `md:w-[4.5rem]` (72 px) collapsed. 72 px keeps a 40 px
  hit target with 16 px gutters and still fits the 36 px brand mark.
- Toggle: dedicated row under the brand (a button on the brand row cannot fit at
  72 px). `ChevronLeft` rotates 180°; `aria-expanded`, `aria-controls="app-sidebar"`,
  dynamic label. One property animates: `transition-[width] duration-150`.
- Max width stays constant when collapsing. Collapse only buys real content width
  below a 1408 px viewport; above it the 1088 px measure is unchanged, so text
  never reflows twice.
- Files: `(app)/layout.tsx`, `components/layout/Sidebar.tsx`, new
  `components/layout/sidebar-toggle.tsx`, new `stores/ui-store.ts`.

### 3.2 Landing (`/`)

| # | Element | Now | Problem | Change | P |
|---|---|---|---|---|---|
| L1 | Hero top | navbar 66 + `pt-20` (80) → **h1 at 190 px** (measured) | ~1/4 of a 800 px laptop screen before the headline | `pt-10` (40) → h1 ≈ 150 px | P0 |
| L2 | Hero text stack | 20 / 20 / 32 / 16 px gaps | 88 px of gaps inside a ~300 px block | 12 / 16 / 24 / 12 → −24 px | P0 |
| L3 | Section gaps | 96 / 112 / 112 (measured) | Two different values; every heading gets 2.4–2.8× more space above than below | 80 everywhere; heading → content 32 | P0 |
| L4 | Content rails | 768 / 896 / 1024 / 1152 | Edges shift up to 128 px between sections; nav and footer are wider than every section | One `max-w-5xl` rail; hero text `max-w-3xl`, subcopy `max-w-xl` | P1 |
| L5 | Hero → features | `pb-16` + `mt-24` = **160 px** of empty background | Largest single gap on the page | `pb-10` + `mt-16` = 104 px | P1 |
| L6 | Bento stretch | first card `sm:col-span-2`; grid rows stretch to tallest cell | ~40–60 px of blank at the bottom of the three short cells | Drop the span (5 equal cells) or `flex h-full flex-col` + `mt-auto` on chips | P2 |
| L7 | Final CTA | `p-10` + 112 above + 96 below | 80 px frame around ~150 px of content | `p-8`, section `mt-20`, card gets `pb-20` before the footer rule | P2 |
| L8 | Reveal margin | `viewport={{ margin: "-80px" }}` | Sections stay invisible until 80 px inside the fold → a blank band while scrolling | `-40px` or `amount: 0.2` | P2 |
| L9 | Grid gutters | HowItWorks `gap-6`, Features `gap-4` | Adjacent 3-column grids do not share column edges | `gap-5` on both | P2 |

### 3.3 Login / Register

| # | Element | Now | Problem | Change | P |
|---|---|---|---|---|---|
| A1 | Page alignment | `min-h-screen justify-center` | A 330 px card floats in 1000 px → ~335 px empty above and below; feels like a holding screen | `items-start pt-16 pb-12` — top-weighted, ≈ 124 px to the card | P0 |
| A2 | Double frame | `glass-card p-1` around `<Card ring-1 … max-w-sm>` | Two frames 4 px apart, `max-w-sm` twice → inner card 376 px not 384; radii 21.6 vs 12 are not concentric | Delete the wrapper, let `Card` own the surface | P0 |
| A3 | Interior density | card `py-4`, form `gap-4`, inputs `h-8` | 16 px gutters around a 32 px field read cramped next to the void | pad 24, `gap-5`, inputs `h-10` | P1 |

### 3.4 Dashboard (`/dashboard`)

| # | Element | Now | Problem | Change | P |
|---|---|---|---|---|---|
| D1 | Stat tiles | `p-5`, 36 px value, hint on 1 of 4 → **124 px tall** | Three tiles carry ~20 px of dead space; four 276 × 124 cards for a label + a number | `p-4`, baseline row (label left / value right, 28 px) → **≈ 72 px** (−42 %) | P0 |
| D2 | Hero row | `LatestRoastCard` `h-full justify-between` + `NewRoastTile` 184 px | The promo tile sets the row height; the roast card splits 52 px of slack into two voids | `p-4`, icon `size-9`, ring 64, drop `justify-between` → **≈ 96 px** | P0 |
| D3 | "Your resumes" | starts ≈ **892 px** down (measured) | Below the fold on a 800 px screen; the dashboard's real content needs a scroll | D1 + D2 + S4 → ≈ 700 px | P0 |
| D4 | Section rhythm | outer `space-y-4`, inner `space-y-4` duplicated, headings `mb-3` | Every boundary is 16 px, so stats / hero / lists read as one flat stack | 24 between sections, 16 inside groups, headings `mb-2` | P1 |
| D5 | Recent roasts | 4 identical 86 px cards | No scanning landmarks | `divide-y` container, 64 px rows, ring 40 | P1 |
| D6 | Empty placeholder | `h-full p-6` dashed box ≈ 760 × 112 | One sentence in a half-page box | Let the CTA tile span 3 columns and delete the placeholder | P2 |

### 3.5 History (`/history`)

| # | Element | Now | Problem | Change | P |
|---|---|---|---|---|---|
| H1 | Roast rows | 86 px each, `gap-3`, no `limit` → 20 rows by default | 20 × 86 + 19 × 12 = **1948 px** — 2.3 screens of identical cards; the 52 px ring sets the height while the text needs 44 | `size="sm"`, ring 40, `divide-y` one container, 56–64 px rows → **≈ 1120 px** (−43 %) | P0 |
| H2 | Paging | none — roasts past #20 are unreachable | A 20-row page is the only density offered | `limit=10` + "Load more" using the existing `offset` | P1 |
| H3 | Days | no grouping | 14 rows all read as one undifferentiated list | Month/day group labels (`text-xs`, `mt-6 mb-2`) | P2 |
| H4 | Tab gap | root `gap-2` **plus** `TabsContent mt-4` = 24 px | 24 here, 12 under dashboard headings | Root `gap-3`, delete `mt-4` | P1 |
| H5 | Empty state | `max-w-md p-8` centred block in a 1152 px column | 448 px block, 704 px of empty gutter | Full-width dashed panel `py-12` inside tabs | P2 |

### 3.6 Analytics (`/analytics`)

| # | Element | Now | Problem | Change | P |
|---|---|---|---|---|---|
| N1 | Score trend | 314 px tall card for 14 points; **line not rendering** (dots only) | Fails its one job: showing a trend; huge empty plot area | Fix the stroke (gotcha 37), then `h-64` and denser ticks | P0 |
| N2 | Stat tiles | same component as dashboard (124 px) | Same dead space, repeated | Reuse the compact tile from D1 | P1 |
| N3 | Activity list | 342 px card next to a 342 px card with unequal content | The shorter column leaves a visible hole at the bottom | Let the list grow to match, or make the pair `items-start` | P2 |
| N4 | Page height | content ends at 934 / 1000 | Only 66 px dead — this page is fine | No action beyond N1/N2 | — |

### 3.7 Upload (`/upload`)

| # | Element | Now | Problem | Change | P |
|---|---|---|---|---|---|
| U1 | Form width | **1088 px** | A 6-field form stretched to full width; the dropzone is 1088 × 196 and the CTA is a 1088 px bar | `mx-auto w-full max-w-2xl` (672) | P0 |
| U2 | Dead space | content ends at **562** / 1000 | **438 px of empty viewport** — the loudest instance of the complaint | U1 + U3 + U4 → ≈ 700 px used, and the page stops looking unfinished | P0 |
| U3 | Dropzone | `p-10`, 56 px icon, ≈ 196 px tall | 80 px of padding for two lines | `p-6 sm:p-8`, icon 48, ≈ 150 px | P1 |
| U4 | Mode grid | `grid-cols-2`, 540 px per card, 2 rows | 132 px of vertical space for four short labels | `sm:grid-cols-4` → one row (−70 px) | P1 |
| U5 | Form rhythm | `space-y-6` throughout | 72–120 px between stacked blocks; the layout jumps when the file chip mounts | `space-y-4`, `space-y-6` only above submit | P1 |

### 3.8 Profile (`/profile`)

| # | Element | Now | Problem | Change | P |
|---|---|---|---|---|---|
| P1 | Identity card | `p-8`, centred, 80 px avatar, **252 px** tall and 1088 wide | Three facts in a billboard | Horizontal row: `p-5`, avatar 56, name/email left, "member since" right → **≈ 96 px** (−62 %) | P0 |
| P2 | Settings | two `p-5` cards, log-out button ~560 px wide | 224 px for two controls; two borders for two rows | One card with `divide-y`; rows `px-5 py-3`; button `w-auto` → **≈ 96 px** | P0 |
| P3 | Dead space | content ends at **506** / 1000 | 494 px of empty screen | P1 + P2 → ≈ 330 px content, page reads complete | P0 |
| P4 | Inline error | hand-rolled `p-6` block, Retry with **0 px** gap | Two centred panels use `p-6` and `p-8`; retry hugs the text | Use `ErrorState` (has `mt-4`) | P2 |

### 3.9 Result (`/analysis/[id]`) — the big one

| # | Element | Now | Problem | Change | P |
|---|---|---|---|---|---|
| R1 | Page header | "Your roast" + `mb-8`, then the scorecard repeats a title 88 px lower | Two titles, 88 px of chrome before the score | Drop `PageHeader` on completed; move "Roast another" into the scorecard header | P0 |
| R2 | Breakdown card | `p-6`, 5 AI category rows | Re-prints the four scores already in the scorecard; ≈ 440 px tall, ~270 px duplicate | Delete the `ai_categories` block, keep deterministic checks (`p-4`) → ≈ 170 px | P0 |
| R3 | Findings | 3 separate `p-6` cards | 144 px of padding + 40 px of gaps for three short lists | One card `p-5`, sections split by `border-t pt-4` | P0 |
| R4 | Prose measure | 14 px across 1024 px → **120–140 chars/line** | Roughly double a readable measure; this is why the roast feels like a wall | `text-[15px] leading-7 max-w-[68ch]` | P0 |
| R5 | Card padding | `p-6 sm:p-8` on 9 cards | 32 px × 9 = 288 px of padding before any nested box | `p-5 sm:p-6` (24) | P1 |
| R6 | Nesting | card `p-8` → fix `p-4` → before/after `p-3` | Body text 60 px inside three borders; ~80 px of each fix is padding | `p-5 sm:p-6` / `p-3` / `p-2.5` | P1 |
| R7 | Section gaps | root `space-y-5` on 9 cards | 160 px of pure gap | `space-y-3` (12) → 96 px | P1 |
| R8 | Micro-labels | 8 mono-uppercase recipes, ~27 rendered instances with real data | Four labels stack before any content in the Reality Check; the stamp stops meaning anything | Keep 2 (scorecard eyebrow + section `h3`), sentence-case the rest, tracking 0.2em → 0.08em | P1 |
| R9 | Score ring | `size={150}` + verdict column = 214 px | Sets the scorecard height at every width | 120 px, verdict on one line | P2 |
| R10 | Expert verdicts | 4 bordered boxes inside a bordered card | 5 borders for 4 short paragraphs | `divide-y` rows, no inner border | P2 |
| R11 | Length | **6076 px** | ~7.6 screens; two sections are duplicate height | R2 + R3 + R5–R7 → estimate **≤ 5,200 px** | P0 |

Optional, after the compression lands: at `≥1280px`, split the page into a
sticky left rail (score + verdict + "roast another", 320 px) and a 720 px prose
column. This is a layout change, not a spacing change — do it only if the page
still feels long after R1–R11.

### 3.10 Runtime pages (running / failed)

`StageProgress` is a `p-8` card with an 8 px progress bar **and** a 5-row stage
list encoding the same progress → ~500 px tall in a 448 px column.
Change: `p-6`, rows `py-1.5`, or drop the bar and keep the list.

---

## 4. Bugs to fix in the same pass

| # | Bug | Evidence | Fix |
|---|---|---|---|
| B1 | Light-mode scores unreadable | `text-yellow-500` on white = **1.91:1**; 60/69 numerals and ring arcs nearly invisible | Add a light-mode variant for the score tones (darker amber, e.g. `oklch(0.55 0.13 70)`) |
| B2 | Analytics trend has no line | 1440 px screenshot shows dots only; `Area stroke="var(--color-score)"` | Verify the computed `stroke` in the DOM; set an explicit `var(--chart-1)` if the config var is not resolving |
| B3 | Light-mode primary text fails AA | `--primary` as text **3.77:1**, white on primary **3.83:1** | Darken `--primary` in light mode or use it as background only |

---

## 5. Phased plan

Each phase is independently shippable and verifiable.

### Phase 0 — Tokens and primitives (½ day)

1. Add the spacing scale documentation comment to `globals.css`; no functional change.
2. Normalise radii to 4 / 8 / 12.
3. Add container variants (`wide` 1152, `prose` 720, `form` 672) as a small
   `PageContainer` component or a `data-width` attribute on `<main>`.
4. `PageHeader`: `mb-4 md:mb-6`, `items-start`, optional `className`.
5. `Card`: adopt `size="sm"` where a card is a row (lists, not panels).

**Done when:** every page uses one of the three widths; no page has 4 different
paddings for the same role.

### Phase 1 — Shell and sidebar (1 day)

S1–S5, S10–S12. Collapsible rail, persisted, hydration-safe, `lg:` breakpoint,
tighter top offset, skip link.

**Done when:** the sidebar toggles 256 ↔ 72 and survives reload; first content
sits ≤ 100 px from the top at 1440; 768–1023 px uses the mobile header; no
hydration warning in the console.

### Phase 2 — Density on data pages (1 day)

D1–D3, H1–H2, H4, N1–N2, P1–P3, U1–U5.

**Done when:** 10 history rows fit a 900 px screen; upload and profile fill at
least ~65 % of a 1000 px viewport; dashboard's "Your resumes" is visible without
scrolling at 900 px.

### Phase 3 — Result page compression (1–1.5 days)

R1–R8, R11, B1.

**Done when:** the result page is ≤ 5,200 px at 1440 for the same analysis;
prose measure ≤ 75 characters; the four category scores appear exactly once.

### Phase 4 — Marketing and auth polish (½–1 day)

L1–L9, A1–A3.

**Done when:** hero h1 at ≤ 160 px; all section gaps are 80; every marketing
section shares one rail; auth pages are top-weighted.

### Phase 5 — Verification (½ day)

- Screenshots at 1440, 1280, 1024, 390 in dark **and** light.
- Re-measure the same metrics as this audit (page height, first-content offset,
  measure in characters, dead space at the bottom).
- `npx tsc --noEmit`, `npm run lint`, `npm run build`.
- Contrast re-check for every score tone in both themes.

---

## 6. Targets

| Metric | Today | Target |
|---|---|---|
| First content offset, app pages | 120 px | ≤ 92 px |
| Landing h1 top | 190 px | ≤ 160 px |
| Upload dead space at 1000 px | 438 px | ≤ 250 px |
| Profile dead space at 1000 px | 494 px | ≤ 300 px |
| History page height (14 rows) | 1588 px | ≤ 1200 px |
| Result page height | 6076 px | ≤ 5200 px |
| Result prose measure | 120–140 chars | 65–75 chars |
| Radius values in use | 12 / 16.8 / 21.6 | 4 / 8 / 12 |
| Section gap values | 96 / 112 / 112 | 80 marketing, 24 app |
| Sidebar states | 1 (256) | 2 (256 / 72), persisted |

---

## 7. Out of scope / open questions

- **Colour and type direction** — separate brand pass; this plan only fixes the
  three contrast bugs that are defects rather than taste.
- **Two-column result layout** — optional Phase 3 extension, above.
- **Server-side rendering of the collapsed state** — a cookie + server wrapper
  would remove the one-frame flash entirely, at the cost of splitting
  `(app)/layout.tsx` into server + client shells. Not worth it for one frame.
- **`frontend/package.json` has no `check` script** even though `AGENTS.md`
  requires `npm run check`; the root script calls lint + build directly. Worth
  aligning while touching the tooling.

---

## 8. Verification log for this audit

Commands actually run, and what they produced:

- `npm run dev` (frontend) → ready in 7.7 s on `localhost:3000`.
- `uvicorn app.main:app --host 127.0.0.1 --port 8000` → `/health` `{"status":"ok"}`;
  demo user reconciled at startup.
- Headless Chrome via CDP, 1440 × 1000, authenticated as the demo user:
  `docH` per page — landing 2399, dashboard 1321, history 1588, analytics 1000,
  upload 1000, profile 1000, result 6076. `h1` top: 190 (landing), 32 (app pages).
  Landing section gaps: 96 / 112 / 112. App content width: 1088 px.
- Upload form box: top 120, height 442 → ends 562.
- Python contrast probe: `yellow-500` on white **1.91:1**, on paper **1.83:1**;
  light `--primary` as text **3.77:1**; white on light `--primary` **3.83:1**;
  dark pairs 6.5–9.8:1.
- Visual review of every route at 1440 in dark, plus dashboard and result in light.

---

## 9. What shipped (2026-11-04)

### Measured before → after

| Page | Before | After | Notes |
|---|---|---|---|
| Landing | 2399 px, h1 at 190 | 2143 px, h1 at **142** | one 80 px section rhythm, one 1024 px rail |
| Dashboard | 1321 px, content ends 1289 | **1000 px**, content ends 814 | stats 124 → ~72, hero row 184 → ~96 |
| History | 1588 px | **1000 px**, content ends 751 | 60 px divided rows, `limit=10` + Load more |
| Analytics | 1000 px | 1000 px, content ends 824 | trend line now paints; tiles compact |
| Upload | form 1088 wide, ends 562 | form **672** wide, ends 438 | 438 px of viewport still empty — a short form |
| Profile | content ends 506 | content ends **337** | identity 252 → 96, two cards → one |
| Result | 6076 px | **4993 px** (−17.8 %) | full-width prose, ~132 characters/line |
| Login | card top ~335 | card top **124** | top-weighted, single frame |
| App pages | first content 120 | **92** | `py-5` + `mb-4` |

### Deviations from the targets

1. **The prose cap was removed at the user's request.** The first pass set
   `max-w-[35rem]` (560 px ≈ 71 characters); the user asked for the full card
   width instead. Prose now fills the content box — 1038 px ≈ 132 characters
   per line — which shortens the page to 4993 px but is well past the 60–75
   character reading ideal. If that becomes tiring, the levers are a larger
   body size (16–17 px), a two-column report, or reinstating a cap.
2. **Upload still has ~438 px below the fold.** Narrowing the form removed the
   stretched-canvas problem, but a five-field form does not fill a 1000 px
   viewport at any sane width. Filling it needs a second column of content,
   which is a product decision, not a spacing fix.
3. **History rows are 60 px, not the projected 56.** The 40 px score ring sets
   the row height. Ten rows still fit above the Load-more button.

### Not done (deliberately)

- Two-column result layout with a sticky score rail — optional Phase 3
  extension; the single column now reads at a sane measure.
- Compact/comfortable density toggle — the compact density became the default.
- Colour and type direction — separate brand pass, unchanged by this work.

### Post-implementation QA (same day)

The first pass checked page geometry, not row composition. A second pass fixed:

- **Analytics activity rows** — badge and date now sit in a defined structure
  (title + date stacked; status badge alone on the right) instead of floating.
- **Badge hierarchy** — `Ready` / `Parsed` are `secondary` (quiet); failures stay
  red. Ember is reserved for scores and CTAs.
- **Trend chart** — `isAnimationActive={false}` on Area/Bar guarantees the line
  paints (the mount animation could leave the area clipped); the x-axis prints a
  day once and blanks repeats (Oct 29 / Oct 30 / Nov 2, not 11 × Oct 30).
- **Light-mode score rings** — `score-ring.tsx` had its own `scoreTone` still on
  `yellow-500` (1.91:1); now `amber-700 dark:yellow-500`.
- **Equal stat tiles** — `auto-rows-fr`, so the tile with a hint no longer sets a
  ragged row.

Interaction tests: sidebar 256 → 72 → 256; Load more 10 → 14 rows; Resumes tab
renders (Radix needs a real pointer event — `.click()` does not activate it);
theme switch applies `.light`; mobile sheet opens. A rendered-contrast audit of
every text leaf on all nine routes, light and dark, returns zero AA failures.

### Verification actually run

`npx tsc --noEmit` clean · `npm run lint` 0 problems · `npm run build` ✅ 10
routes · headless Chrome at 1440 × 1000 and 390 × 844: no horizontal overflow
on dashboard, history, upload or result; collapsed sidebar measured at 72 px;
analytics line and area visible in a 1440 px capture.
