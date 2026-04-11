# FitGlyph — Claude Code Design Constitution

> **PRIME DIRECTIVE:** You are not building a generic fitness app. You are building a precision data tool for someone with a background in data science and analytics. Every UI decision should reflect that. If something looks like it belongs in a SaaS starter template, it is wrong.

***

## Project Context

**App:** FitGlyph — gym log and fitness tracker
**Owner:** Peyton Ramsey (data scientist, M.S. Business Analytics)
**Aesthetic target:** Athletic editorial × data-dense precision. Think Linear.app's information density meets Strava's earned-progress feeling — not another dark-mode health app with colored icon tiles.
**User:** Someone who reads data for a living and runs Division I cross country. The UI should feel like it was designed for them specifically.

***

## WORKFLOW — Follow This Order, No Exceptions (Method 2)

For **any new screen, component, or significant UI change**, execute these phases in sequence:

1. **BRIEF PHASE** — Write a design brief in plain English. No code. Include: mood, layout principle, what this should NOT look like. Wait for approval before proceeding.
2. **TOKEN PHASE** — Output only CSS custom properties (`:root { }`). No HTML. No components. Wait for approval.
3. **BUILD PHASE** — Build against the approved brief and tokens only.

> **Do not skip or combine phases.** If asked to "just build it quickly," still output a 3-sentence brief first.

***

## DESIGN TOKENS — Locked (Method 1 + Method 3)

Do not deviate from these values. Do not introduce new colors, fonts, or radius values without explicit instruction.

### Typography
```
Display font : Cabinet Grotesk (Fontshare) — headings only, 24px minimum
Body font    : Satoshi (Fontshare) — all body, labels, UI chrome
Scale        : xs=12px, sm=14px, base=16px, lg=20px, xl=28px, 2xl=40px
```
- Left-align **everything** by default. Center-align only single-line hero numbers.
- Weight does the hierarchy work, not size jumps. Bold numbers, regular labels.
- Tabular numerals (`font-variant-numeric: tabular-nums`) on all stats and metrics.

### Color
```
Background stack : #0f0e0d → #161513 → #1c1b19
Border           : oklch(from #cdccca l c h / 0.10) — alpha only, never solid gray
Text primary     : #cdccca
Text muted       : #797876
Text faint       : #5a5957
Accent (ONE)     : #4f98a3 — used ONLY for primary CTAs and active states
Success          : #6daa45 — for completed workouts / PR indicators only
Warning          : #bb653b — for muscle balance alerts only
```
> **One accent color. That is all.** Hierarchy comes from spacing, weight, and surface contrast — not multiple colors.

### Surface & Radius
```
Card border-radius  : 10px
Input border-radius : 6px
Chip/badge          : 9999px (pill only)
Button              : 6px
```
- Inner radius = outer radius − gap (enforce the nested radius formula always)
- Surface depth via background color shifts, never via colored borders

### Shadows
```
Elevated card : 0 1px 2px oklch(0 0 0 / 0.20), 0 4px 16px oklch(0 0 0 / 0.14)
Hover lift    : 0 2px 4px oklch(0 0 0 / 0.28), 0 12px 32px oklch(0 0 0 / 0.18)
```

***

## ANTI-PATTERNS — Never Do These (Method 3)

These patterns are explicitly banned. If a component you are about to build would include any of these, stop and redesign it first.

### Color & Surface
- [ ] Gradient buttons (`background: linear-gradient(...)` on any button)
- [ ] Gradient text (`background-clip: text`)
- [ ] Multiple colored accents in a single viewport (orange, red, yellow, teal simultaneously)
- [ ] Purple, violet, indigo, or blue-to-purple color schemes
- [ ] Glowing orbs or decorative background blobs

### Layout
- [ ] 3-column symmetrical grids of equal-weight cards with icon + title + description
- [ ] Center-aligned body text, card descriptions, or metric labels
- [ ] Every section the same height and padding — vary rhythm intentionally
- [ ] Uniform bubbly border-radius on all elements

### Decoration
- [ ] **Icons inside colored circles or rounded squares** — this is the #1 giveaway. Icons sit at natural size, no backgrounds.
- [ ] Colored side-borders on cards (`border-left: 3px solid <color>`)
- [ ] Decorative dividers, wavy SVG section separators, or floating shapes
- [ ] Emoji as UI elements or bullet replacements
- [ ] Background grid/dot patterns as decoration

### Copy
- [ ] Generic dashboard labels: "Welcome back!", "Let's get moving!", "Your journey"
- [ ] Vague metric descriptions — be specific and data-precise

***

## FITGLYPH-SPECIFIC DESIGN LANGUAGE (Method 5)

Leverage Peyton's data science background as the primary design principle.

### Numbers are the hero
- Metric values should be the **largest visual element** on any data screen, not the label
- Pattern: `large number` + `small unit` + `tiny label below` — not `ICON [colored chip] LABEL: value`
- Example: `247` in 40px Satoshi bold, `lbs` in 16px muted, `total volume` in 12px faint below

### Data density over decoration
- The calendar is a **volume heatmap** — not a generic date picker. Use opacity of the accent color to show training load per day (0 sessions = surface, max sessions = full accent).
- The workout log history is a **trend story** — show progressive overload as a sparkline next to each lift, not just a list of past sessions.
- Muscle balance warnings (like "Check Core — 13 days ago") are **high-signal alerts** that deserve a dedicated, data-rich surface — not just a warning chip in a corner tile.

### Information hierarchy per screen
```
Level 1 (immediate): Today's key number — what matters right now
Level 2 (context): Trends and streaks — am I progressing?
Level 3 (detail): Drill-down — history, set-by-set, nutrition breakdown
```
Never mix all three levels on one screen without clear visual separation.

***

## CRITIQUE PASS — Run Before Showing Me (Method 4)

After building any screen or component, before outputting the result, run this internal check:

```
Review what you just built. For each of the following, answer YES or NO:
1. Does any element look like it belongs in a generic SaaS template?
2. Does any element violate an anti-pattern from the ANTI-PATTERNS list above?
3. Are numbers visually dominant over their labels on data screens?
4. Is the accent color used more than once per viewport for non-CTA purposes?
5. Are there any centered text blocks that should be left-aligned?

If any answer is YES — fix it before outputting. Do not ask me to approve broken work.
```

***

## REFERENCE AESTHETICS

When making judgment calls, ask: does this look more like (A) or (B)?

| (A) — Target | (B) — Avoid |
|---|---|
| Linear.app sidebar | Generic dark SaaS nav |
| Strava activity summary | MyFitnessPal dashboard |
| GitHub contribution heatmap | Colored tile grid |
| Runner's World data feature | Generic health app |
| Vercel deployment card | Material Design stat card |

Always aim for (A).

***

## GENERAL CODING RULES

- No `localStorage` or `sessionStorage` — use in-memory state
- All external links: `target="_blank" rel="noopener noreferrer"`
- Every `<img>` needs `alt`, `width`, `height`, `loading="lazy"`
- Semantic HTML only — `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<footer>`
- One `<h1>` per page, heading hierarchy never skips levels
- All interactive elements: minimum 44×44px touch target
- `prefers-reduced-motion` respected on all animations
- `font-variant-numeric: tabular-nums` on all numeric displays

## Session Bootstrap
At the start of every session, read these files before doing anything:
- DESIGN_BRIEF.md — the approved design brief, do not deviate from it
- PROGRESS.md — check what screens are done, resume from the next unchecked one