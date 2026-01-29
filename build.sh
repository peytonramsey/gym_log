#!/usr/bin/env bash
# Render build script

set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations using Python script (more reliable than flask CLI)
echo "Running database migrations..."
python run_migrations.py

echo "✓ Build completed successfully!"
