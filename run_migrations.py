"""
Run database migrations in production
"""
from flask_migrate import upgrade
from app import app, initialize_app

with app.app_context():
    print("Running database migrations...")
    upgrade()
    print("✓ Migrations completed successfully!")

    # Initialize app after migrations complete
    print("Initializing app (admin user, cleanup)...")
    initialize_app()
    print("✓ Initialization completed!")
