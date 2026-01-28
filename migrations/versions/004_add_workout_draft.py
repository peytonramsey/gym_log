"""Add is_draft column to workout table for draft saving

Revision ID: 004_add_workout_draft
Revises: 003_make_weight_nullable
Create Date: 2026-01-28 10:00:00.000000

This migration adds an is_draft column to the workout table to support
auto-saving workouts in progress. Draft workouts persist across page
navigations and browser refreshes.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_workout_draft'
down_revision = '003_make_weight_nullable'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column already exists (safe migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('workout')]

    if 'is_draft' not in columns:
        with op.batch_alter_table('workout', schema=None) as batch_op:
            batch_op.add_column(sa.Column('is_draft', sa.Boolean(), nullable=False, server_default='0'))
        print("[MIGRATION] Added is_draft column to workout table")
    else:
        print("[MIGRATION] is_draft column already exists, skipping")


def downgrade():
    with op.batch_alter_table('workout', schema=None) as batch_op:
        batch_op.drop_column('is_draft')
    print("[MIGRATION] Removed is_draft column from workout table")
