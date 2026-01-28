"""Add timezone_offset column to users table

Revision ID: 002_add_timezone_offset
Revises: 001_add_template_schedule
Create Date: 2026-01-15 12:00:00.000000

This migration adds a timezone_offset column to the users table to store
user's preferred timezone offset from UTC (e.g., -5 for EST).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_timezone_offset'
down_revision = '001_add_template_schedule'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column already exists before adding it
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'timezone_offset' not in columns:
        op.add_column('users', sa.Column('timezone_offset', sa.Integer(), nullable=True))

        # Set default value to 0 (UTC) for existing users
        conn.execute(sa.text("UPDATE users SET timezone_offset = 0 WHERE timezone_offset IS NULL"))

        print("[MIGRATION] Added timezone_offset column to users table")
    else:
        print("[MIGRATION] timezone_offset column already exists, skipping")


def downgrade():
    # Check if column exists before dropping it
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'timezone_offset' in columns:
        op.drop_column('users', 'timezone_offset')
        print("[MIGRATION] Dropped timezone_offset column from users table")
    else:
        print("[MIGRATION] timezone_offset column doesn't exist, skipping drop")
