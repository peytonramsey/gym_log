"""
Migration script to add set_data column to Exercise table
"""
import sqlite3
import os

db_path = 'instance/gymlog.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(exercise)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'set_data' not in columns:
            print("Adding set_data column to exercise table...")
            cursor.execute("ALTER TABLE exercise ADD COLUMN set_data TEXT")
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("set_data column already exists, skipping migration.")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()

    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}. Will be created on first run.")
