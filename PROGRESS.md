# FitGlyph — Redesign Progress

Tracking every screen against the CLAUDE.md design constitution.
See DESIGN_BRIEF.md for the approved mood, typography, and anti-pattern rules.

---

## Foundation

- [x] Design audit (logic, components, CSS inventory)
- [x] Design brief (mood, typography hierarchy, Level 1/2/3 structure)
- [x] `base.html` — master layout: navbar, bottom nav, toast system, font imports, body background

---

## Screens

- [x] `index.html` — Home dashboard (Level 1/2/3 hierarchy, weekly heatmap, compact nav)
- [x] `log.html` — Workout logging (exercise input, superset/drop-set cards, autocomplete)
- [x] `history.html` — History & calendar (volume heatmap calendar, compare mode, activity cards)
- [x] `progress.html` — Exercise progress (per-exercise charts, delta badges, template selector)
- [x] `body_metrics.html` — Body metrics (weight trend, goal predictor, macro results)
- [x] `schedule.html` — Template management (template cards, create/edit modal, color system)
- [x] `nutrition.html` — Nutrition logging (meal tabs, food search, macro summary)
- [x] `settings.html` — Settings (preferences, exercise normalization, account)
- [x] `login.html` — Authentication
- [x] `register.html` — Registration


---

## Notes

- `base.html` must be redesigned before any screen is considered final — it controls the navbar, bottom nav, and body background that all screens inherit.
- Template color system (used in `schedule.html`, `history.html`, `progress.html`) needs a design decision: the current 8-color-per-template system conflicts with the single-accent rule. Resolve before those screens.
- `localStorage` usage for theme and timezone lives in `base.html` — address when that screen is tackled.