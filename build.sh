#!/usr/bin/env bash
# Render build script

set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Initialize database tables
python init_db.py
