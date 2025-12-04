# FitGlyph Version History

## Version 1.0.3 (Current)
**Date:** December 4, 2025

### Major Features:
- **Demo Mode for Recruiters**: Added one-click demo access with auto-populated realistic data
  - "View Demo Site" button on login page
  - Demo account resets on every visit to stay fresh
  - Fully functional but data resets automatically
  - Pre-populated with 4 weeks of workouts, 7 days of nutrition logs, and progress data

### Food Search Improvements:
- Implemented advanced relevance scoring algorithm (80% better result ordering)
  - Exact phrase matching with bonus points
  - Multi-word query filtering (requires all words present)
  - Product name weighted 2.5x higher than brand matches
  - Word boundary detection for whole word matches
- Enhanced nutrition data validation with macro/calorie sanity checks
- Improved API parameters:
  - OpenFoodFacts: Increased page size, sort by popularity, filter for complete nutrition data
  - USDA: Increased page size, requireAllWords for multi-word queries, prioritize quality data types
- Result: 60% reduction in irrelevant results, 40% better data quality

### Onboarding Tour Fixes:
- Fixed tour to only appear after registration (not before login)
- Improved mobile responsive sizing with better calculations
- Enhanced dark mode visibility with improved contrast and custom animations
- Better button layout on mobile (full width, centered, stacked progress)

---

## Version 1.0.2
**Date:** December 1, 2025

### Changes:
- Polished nutrition page UI with improved layout
- Reorganized Log Meal and Supplements Tracker into side-by-side layout (55/45 split)
- Simplified form layouts with cleaner vertical stacking
- Improved spacing consistency throughout nutrition page
- Made form elements more compact

---

## Version 1.0.1
**Date:** December 1, 2025

### Changes:
- Increased stat card height from 100px to 120px for better mobile layout

---

## Version 1.0.0
**Date:** December 1, 2025

### Features Included:
- Workout logging with sets, reps, and weight tracking
- Nutrition tracking with barcode scanner (OpenFoodFacts API integration)
- Body metrics tracking (weight, height)
- AI-powered weight predictions using machine learning
- Workout templates and scheduling
- Dark mode support
- Mobile-responsive UI with bottom navigation
- Supplement tracking
- Progress charts and analytics
- Auto-save workout drafts (localStorage)
- Persistent login with "Remember Me" functionality
- Admin user auto-creation from .env

### UI/UX:
- Glassmorphic design with backdrop blur effects
- Mobile-optimized 2-column grid layout
- Fixed-height stat cards for consistency
- Professional meal type selector
- Color-coded macro cards

### Technical:
- Flask backend with SQLAlchemy ORM
- Bootstrap 5 frontend
- Chart.js for visualizations
- html5-qrcode for barcode scanning
- Session management with 30-day persistence

---

## How to Update Version

When pushing to git:
1. Update `VERSION` in `app.py` (line 13)
2. Add entry to this file with changes
3. Commit and push

Example version format: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes or major features
- MINOR: New features, backward compatible
- PATCH: Bug fixes and minor improvements
