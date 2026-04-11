"""Add IANA timezone column to users table

Revision ID: 010_add_iana_timezone
Revises: 009_add_rest_day
Create Date: 2026-04-11

Adds a `timezone` VARCHAR(64) column to store an IANA timezone name
(e.g. "America/New_York").  The existing `timezone_offset` integer column
is kept unchanged so all existing server-side arithmetic still works; the
POST /api/user/timezone route keeps both columns in sync automatically.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = '010_add_iana_timezone'
down_revision = '009_add_rest_day'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('users')]
    if 'timezone' not in columns:
        op.add_column(
            'users',
            sa.Column('timezone', sa.String(64), nullable=True, server_default='UTC')
        )
        print("[MIGRATION] Added timezone column to users table")
    else:
        print("[MIGRATION] timezone column already exists, skipping")


def downgrade():
    op.drop_column('users', 'timezone')
    print("[MIGRATION] Dropped timezone column from users table")
