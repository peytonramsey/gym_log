#!/usr/bin/env bash
# Render build script

set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
flask db upgrade

echo "✓ Build completed successfully!"
