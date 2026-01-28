"""Make weight column nullable for bodyweight exercises

Revision ID: 003_make_weight_nullable
Revises: 002_add_timezone_offset
Create Date: 2026-01-15 14:00:00.000000

This migration makes the weight column in the exercise table nullable
to support bodyweight exercises (push-ups, pull-ups, cardio, etc.)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_make_weight_nullable'
down_revision = '002_add_timezone_offset'
branch_labels = None
depends_on = None


def upgrade():
    # Make weight column nullable
    with op.batch_alter_table('exercise', schema=None) as batch_op:
        batch_op.alter_column('weight',
                              existing_type=sa.Float(),
                              nullable=True)

    print("[MIGRATION] Made weight column nullable in exercise table")


def downgrade():
    # Make weight column NOT NULL again
    # First, update any NULL values to 0
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE exercise SET weight = 0 WHERE weight IS NULL"))

    with op.batch_alter_table('exercise', schema=None) as batch_op:
        batch_op.alter_column('weight',
                              existing_type=sa.Float(),
                              nullable=False)

    print("[MIGRATION] Made weight column NOT NULL in exercise table")
