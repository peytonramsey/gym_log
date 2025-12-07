# Database Migration Helper Script for FitGlyph (PowerShell)
# This script simplifies common database migration tasks on Windows

param(
    [Parameter(Position=0)]
    [string]$Command,

    [Parameter(Position=1)]
    [string]$Argument
)

# Colors for output
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# Main commands
switch ($Command) {
    "init" {
        Write-Warning-Custom "Initializing Flask-Migrate (only run once)"
        docker-compose exec web flask db init
        Write-Success "Migration folder created"
    }

    "migrate" {
        $Message = if ($Argument) { $Argument } else { "Database schema update" }
        Write-Warning-Custom "Creating new migration: $Message"
        docker-compose exec web flask db migrate -m "$Message"
        Write-Success "Migration created. Review it in migrations/versions/"
    }

    "upgrade" {
        Write-Warning-Custom "Applying migrations to database"
        docker-compose exec web flask db upgrade
        Write-Success "Database upgraded successfully"
    }

    "downgrade" {
        Write-Error-Custom "Downgrading database (rolling back last migration)"
        $confirm = Read-Host "Are you sure? This will undo the last migration. (yes/no)"
        if ($confirm -eq "yes") {
            docker-compose exec web flask db downgrade
            Write-Success "Database downgraded"
        } else {
            Write-Warning-Custom "Downgrade cancelled"
        }
    }

    "current" {
        docker-compose exec web flask db current
    }

    "history" {
        docker-compose exec web flask db history
    }

    "backup" {
        $BackupFile = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
        Write-Warning-Custom "Creating database backup: $BackupFile"
        docker-compose exec -T db pg_dump -U fitglyph_user fitglyph_db | Out-File -FilePath $BackupFile -Encoding UTF8
        Write-Success "Backup created: $BackupFile"
    }

    "restore" {
        if (-not $Argument) {
            Write-Error-Custom "Please specify backup file: .\migrate.ps1 restore backup.sql"
            exit 1
        }

        $BackupFile = $Argument

        if (-not (Test-Path $BackupFile)) {
            Write-Error-Custom "Backup file not found: $BackupFile"
            exit 1
        }

        Write-Error-Custom "DANGER: This will DELETE all current data and restore from backup"
        $confirm = Read-Host "Are you absolutely sure? Type 'DELETE ALL DATA' to confirm"

        if ($confirm -eq "DELETE ALL DATA") {
            Write-Warning-Custom "Stopping web container..."
            docker-compose stop web

            Write-Warning-Custom "Dropping database..."
            docker-compose exec db psql -U fitglyph_user -c "DROP DATABASE IF EXISTS fitglyph_db;"

            Write-Warning-Custom "Creating fresh database..."
            docker-compose exec db psql -U fitglyph_user -c "CREATE DATABASE fitglyph_db;"

            Write-Warning-Custom "Restoring from backup..."
            Get-Content $BackupFile | docker-compose exec -T db psql -U fitglyph_user fitglyph_db

            Write-Warning-Custom "Starting web container..."
            docker-compose start web

            Write-Success "Database restored from $BackupFile"
        } else {
            Write-Warning-Custom "Restore cancelled"
        }
    }

    default {
        Write-Host "FitGlyph Database Migration Helper" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Usage: .\migrate.ps1 [command] [options]"
        Write-Host ""
        Write-Host "Commands:"
        Write-Host "  init                  Initialize Flask-Migrate (run once)"
        Write-Host "  migrate [message]     Create new migration"
        Write-Host "  upgrade               Apply migrations to database"
        Write-Host "  downgrade             Rollback last migration"
        Write-Host "  current               Show current migration version"
        Write-Host "  history               Show migration history"
        Write-Host "  backup                Create database backup"
        Write-Host "  restore <file>        Restore database from backup"
        Write-Host "  help                  Show this help message"
        Write-Host ""
        Write-Host "Examples:"
        Write-Host "  .\migrate.ps1 migrate 'Add user profile table'"
        Write-Host "  .\migrate.ps1 upgrade"
        Write-Host "  .\migrate.ps1 backup"
        Write-Host "  .\migrate.ps1 restore backup_20241206_153000.sql"
        Write-Host ""
        Write-Warning-Custom "IMPORTANT: Always backup before running migrations!"
    }
}
