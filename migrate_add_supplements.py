"""
Migration script to add the supplements table to existing databases
"""

from app import app, db
from models import Supplement

with app.app_context():
    # Create all tables (will only create missing ones)
    db.create_all()
    print("[OK] Supplements table created successfully!")
    print("The database has been migrated to include supplement tracking.")