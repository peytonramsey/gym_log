#!/bin/bash
# Database Migration Helper Script for FitGlyph
# This script simplifies common database migration tasks

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in Docker or local
if [ -f /.dockerenv ]; then
    DOCKER_CMD=""
else
    DOCKER_CMD="docker-compose exec web "
fi

# Helper functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Main commands
case "$1" in
    init)
        print_warning "Initializing Flask-Migrate (only run once)"
        ${DOCKER_CMD}flask db init
        print_success "Migration folder created"
        ;;

    migrate)
        MESSAGE=${2:-"Database schema update"}
        print_warning "Creating new migration: $MESSAGE"
        ${DOCKER_CMD}flask db migrate -m "$MESSAGE"
        print_success "Migration created. Review it in migrations/versions/"
        ;;

    upgrade)
        print_warning "Applying migrations to database"
        ${DOCKER_CMD}flask db upgrade
        print_success "Database upgraded successfully"
        ;;

    downgrade)
        print_error "Downgrading database (rolling back last migration)"
        read -p "Are you sure? This will undo the last migration. (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            ${DOCKER_CMD}flask db downgrade
            print_success "Database downgraded"
        else
            print_warning "Downgrade cancelled"
        fi
        ;;

    current)
        ${DOCKER_CMD}flask db current
        ;;

    history)
        ${DOCKER_CMD}flask db history
        ;;

    backup)
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        print_warning "Creating database backup: $BACKUP_FILE"

        if [ -f /.dockerenv ]; then
            # Running inside container
            pg_dump -U fitglyph_user fitglyph_db > "/app/$BACKUP_FILE"
        else
            # Running on host
            docker-compose exec -T db pg_dump -U fitglyph_user fitglyph_db > "$BACKUP_FILE"
        fi

        print_success "Backup created: $BACKUP_FILE"
        ;;

    restore)
        if [ -z "$2" ]; then
            print_error "Please specify backup file: ./migrate.sh restore backup.sql"
            exit 1
        fi

        BACKUP_FILE="$2"

        if [ ! -f "$BACKUP_FILE" ]; then
            print_error "Backup file not found: $BACKUP_FILE"
            exit 1
        fi

        print_error "DANGER: This will DELETE all current data and restore from backup"
        read -p "Are you absolutely sure? Type 'DELETE ALL DATA' to confirm: " confirm

        if [ "$confirm" = "DELETE ALL DATA" ]; then
            print_warning "Stopping web container..."
            docker-compose stop web

            print_warning "Dropping database..."
            docker-compose exec db psql -U fitglyph_user -c "DROP DATABASE IF EXISTS fitglyph_db;"

            print_warning "Creating fresh database..."
            docker-compose exec db psql -U fitglyph_user -c "CREATE DATABASE fitglyph_db;"

            print_warning "Restoring from backup..."
            docker-compose exec -T db psql -U fitglyph_user fitglyph_db < "$BACKUP_FILE"

            print_warning "Starting web container..."
            docker-compose start web

            print_success "Database restored from $BACKUP_FILE"
        else
            print_warning "Restore cancelled"
        fi
        ;;

    help|*)
        echo "FitGlyph Database Migration Helper"
        echo ""
        echo "Usage: ./migrate.sh [command] [options]"
        echo ""
        echo "Commands:"
        echo "  init                  Initialize Flask-Migrate (run once)"
        echo "  migrate [message]     Create new migration"
        echo "  upgrade               Apply migrations to database"
        echo "  downgrade             Rollback last migration"
        echo "  current               Show current migration version"
        echo "  history               Show migration history"
        echo "  backup                Create database backup"
        echo "  restore <file>        Restore database from backup"
        echo "  help                  Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./migrate.sh migrate \"Add user profile table\""
        echo "  ./migrate.sh upgrade"
        echo "  ./migrate.sh backup"
        echo "  ./migrate.sh restore backup_20241206_153000.sql"
        echo ""
        print_warning "IMPORTANT: Always backup before running migrations!"
        ;;
esac
