"""
Run database migrations in production
"""
from flask_migrate import upgrade
from app import app

with app.app_context():
    print("Running database migrations...")
    upgrade()
    print("✓ Migrations completed successfully!")
