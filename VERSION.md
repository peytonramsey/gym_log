# FitGlyph Version History

## Version 1.0.1 (Current)
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
