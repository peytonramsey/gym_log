# FitGlyph — Design Brief

## Mood / Aesthetic

FitGlyph should feel like a personal performance report written by someone who trains seriously and reads data for a living — spare, authoritative, and earned, not marketed.

---

## Typography Hierarchy on Data Screens

Three tiers, always in this relationship:

**Tier 1 — The number.** Largest element on screen. Satoshi Bold, 40px. Tabular numerals. No background, no icon competing with it. Example: `247`

**Tier 2 — The unit.** Immediately subordinate to the number. Satoshi Regular, 16px, text-muted (#797876). Inline or directly below. Example: `lbs`

**Tier 3 — The label.** Smallest element. Satoshi Regular, 12px, text-faint (#5a5957). Always below, always left-aligned. Example: `total volume`

The label names the number. The number dominates the label. Most apps reverse this — FitGlyph does not.

---

## Home Dashboard — Level 1 / 2 / 3

**Level 1 — What matters right now (above the fold, full-width).** One dominant number: workouts completed this week out of `user.weekly_goal`. If today has a scheduled template, the template name appears directly beneath as a single line of text — not a card, just text. No charts at Level 1. Everything computed server-side already.

**Level 2 — Am I progressing? (middle, one scroll).** Three data points, not cards — closer to a structured row:

1. Training load this week vs last week — derived from `sets × reps × weight` across `Exercise` records.
2. The current week as a volume heatmap — seven days, accent color (#4f98a3) at varying opacity. Zero sessions = surface. Max sessions = full accent. No per-template color coding.
3. Muscle balance gap — the `ExerciseBank.muscle_group` with the longest gap since last trained, with exact day count. One line of text.

**Level 3 — Drill-down (bottom, requires intent).** Nutrition summary (today's calories vs `NutritionGoals.calories_goal` + three macros) and navigation to History, Progress, Body Metrics. Compact, not equal-weight tiles. The user goes there deliberately.

---

## Three Things This Must NOT Look Like

**1. MyFitnessPal's dashboard.** A grid of colored macro tiles where every nutrient gets its own accent color and its own equal-weight card. In FitGlyph, macros are Level 3 supporting data, not the headline.

**2. A generic dark-mode SaaS page.** Glassmorphic cards on a blurred background, a bottom nav with glowing icons, feature tiles with colored rounded-square icon backgrounds. Nothing here glows, blurs, or uses icons as decoration.

**3. Strava's activity feed misread as a dashboard.** Colored progress rings, achievement badges, segment tiles at equal visual weight. FitGlyph has no rings, no badges, no decorative arcs. Progress is numbers and trend lines.

