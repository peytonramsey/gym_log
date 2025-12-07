# Database Migrations & Data Persistence Guide

This guide explains how to safely update your database schema without losing user data.

---

## 🔒 Your Data is Safe!

**IMPORTANT**: Git pushes DO NOT affect your database or user data.

### What Git Tracks:
- ✅ Python code files (`.py`)
- ✅ HTML templates (`.html`)
- ✅ Configuration files (`docker-compose.yml`, `Dockerfile`)
- ✅ Documentation (`.md` files)

### What Git Does NOT Track:
- ❌ Database data (stored in Docker volumes)
- ❌ User uploads
- ❌ `.env` files (excluded by .gitignore)
- ❌ `instance/` folder with SQLite database

---

## 📦 Flask-Migrate Setup

Flask-Migrate allows you to update your database schema (tables, columns) without losing existing data.

### Installation (Already Done)

Flask-Migrate is already installed in `requirements.txt`:
```
Flask-Migrate==4.0.5
```

### First-Time Setup

If you're starting fresh or haven't initialized migrations yet:

```bash
# 1. Initialize migrations folder (only once)
flask db init

# 2. Create initial migration from current models
flask db migrate -m "Initial migration"

# 3. Apply migration to database
flask db upgrade
```

This creates a `migrations/` folder that tracks database schema changes.

---

## 🔄 Making Database Schema Changes

When you add new tables or modify existing ones (like adding the `TemplateSchedule` table for multi-day scheduling):

### Step 1: Update Your Models

Edit `models.py` to add/modify database models:

```python
# Example: Add new table
class TemplateSchedule(db.Model):
    __tablename__ = 'template_schedule'
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('workout_template.id'))
    day_of_week = db.Column(db.Integer, nullable=False)
```

### Step 2: Create Migration

```bash
# Generate migration script automatically
flask db migrate -m "Add TemplateSchedule table for multi-day workouts"
```

This creates a new migration file in `migrations/versions/` that describes the changes.

### Step 3: Review Migration (Optional but Recommended)

```bash
# Check the generated migration file
ls migrations/versions/
```

Open the newest file to verify it's creating the correct changes.

### Step 4: Apply Migration

```bash
# Apply changes to database
flask db upgrade
```

**Your existing data is preserved!** Only the schema changes.

---

## 🐳 Docker Workflow

### With Docker Compose:

```bash
# Access the running container
docker-compose exec web bash

# Inside container, run migrations
flask db upgrade

# Exit container
exit
```

### Or run directly:

```bash
docker-compose exec web flask db upgrade
```

---

## 🆘 Common Migration Commands

### Check Current Migration Status
```bash
flask db current
```

### View Migration History
```bash
flask db history
```

### Upgrade to Latest Version
```bash
flask db upgrade
```

### Downgrade (Rollback) One Version
```bash
flask db downgrade
```

### Downgrade to Specific Version
```bash
flask db downgrade <revision_id>
```

---

## 💾 Database Backup & Restore

### PostgreSQL (Docker)

#### Backup Database:
```bash
# Create backup file
docker-compose exec db pg_dump -U fitglyph_user fitglyph_db > backup_$(date +%Y%m%d).sql

# Or from host machine
docker-compose exec -T db pg_dump -U fitglyph_user fitglyph_db > backup.sql
```

#### Restore Database:
```bash
# Stop the web container
docker-compose stop web

# Drop and recreate database
docker-compose exec db psql -U fitglyph_user -c "DROP DATABASE fitglyph_db;"
docker-compose exec db psql -U fitglyph_user -c "CREATE DATABASE fitglyph_db;"

# Restore from backup
docker-compose exec -T db psql -U fitglyph_user fitglyph_db < backup.sql

# Restart web container
docker-compose start web
```

### SQLite (Local Development)

#### Backup:
```bash
# Copy the database file
cp instance/gymlog.db instance/gymlog_backup_$(date +%Y%m%d).db
```

#### Restore:
```bash
# Replace with backup
cp instance/gymlog_backup_20241206.db instance/gymlog.db
```

---

## ⚠️ The ONLY Ways You'll Lose Data

1. **Running `docker-compose down -v`** - The `-v` flag deletes volumes (including database)
   - **Safe**: `docker-compose down`
   - **Dangerous**: `docker-compose down -v`

2. **Manually deleting Docker volumes**:
   ```bash
   docker volume rm gymlog_postgres_data  # DON'T DO THIS unless intentional
   ```

3. **Running destructive migrations without backup**:
   - Dropping tables
   - Deleting columns
   - Always backup before major schema changes!

---

## 📋 Best Practices

### 1. Always Backup Before Major Changes
```bash
# Create backup
docker-compose exec -T db pg_dump -U fitglyph_user fitglyph_db > backup_before_migration.sql

# Then run migration
flask db upgrade
```

### 2. Test Migrations Locally First
- Never test migrations directly on production
- Use a local copy of production data to test

### 3. Use Descriptive Migration Messages
```bash
# Good
flask db migrate -m "Add multi-day scheduling support for workout templates"

# Bad
flask db migrate -m "update"
```

### 4. Commit Migrations to Git
```bash
git add migrations/
git commit -m "Add migration for multi-day workout scheduling"
git push
```

The `migrations/` folder should be tracked in git so teammates/deployments get the same schema changes.

---

## 🚀 Production Deployment Workflow

### Initial Deployment:
```bash
# 1. Pull latest code
git pull origin main

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
flask db upgrade

# 4. Restart application
# (Platform-specific, e.g., Render auto-restarts)
```

### Subsequent Deployments:
```bash
# 1. Backup database first!
docker-compose exec -T db pg_dump -U fitglyph_user fitglyph_db > backup.sql

# 2. Pull latest code
git pull origin main

# 3. Rebuild if needed
docker-compose up -d --build

# 4. Run any new migrations
docker-compose exec web flask db upgrade
```

---

## 🔍 Troubleshooting

### "Target database is not up to date"
```bash
# Check current status
flask db current

# Upgrade to latest
flask db upgrade
```

### "Can't locate revision identified by..."
This means migrations folder is out of sync. Solutions:

**Option 1**: Pull latest migrations from git
```bash
git pull origin main
flask db upgrade
```

**Option 2**: Reset migrations (DANGER - only for development)
```bash
# Backup your data first!
# Then delete migrations folder and reinitialize
rm -rf migrations/
flask db init
flask db migrate -m "Recreate initial migration"
flask db upgrade
```

### "Database already has table X"
Your database has tables but no migration history. Solutions:

**Option 1**: Stamp current version (safest)
```bash
# Create migration
flask db migrate -m "Sync existing schema"

# Mark as applied without running
flask db stamp head
```

**Option 2**: Start fresh (development only)
```bash
# Backup data, drop all tables, run migrations fresh
```

---

## 📊 Current Schema Changes (v1.0.4)

### Added:
- `TemplateSchedule` table for multi-day workout scheduling
- Relationship between `WorkoutTemplate` and `TemplateSchedule`
- Support for workouts scheduled on multiple days of the week

### Modified:
- `WorkoutTemplate.day_of_week` - Kept for backwards compatibility but deprecated
- Added `WorkoutTemplate.scheduled_days` relationship

### Migration:
```bash
flask db migrate -m "Add multi-day workout scheduling support"
flask db upgrade
```

---

## 📚 Additional Resources

- [Flask-Migrate Documentation](https://flask-migrate.readthedocs.io/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/) (underlying library)
- [PostgreSQL Backup Guide](https://www.postgresql.org/docs/current/backup-dump.html)

---

**Last Updated**: December 2024
**Version**: 1.0.4 (Multi-day scheduling support)
