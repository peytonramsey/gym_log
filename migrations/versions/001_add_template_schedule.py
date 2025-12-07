"""Add template_schedule table for multi-day workout scheduling

Revision ID: 001_add_template_schedule
Revises:
Create Date: 2024-12-07 11:45:00.000000

This migration is safe for existing databases - it only creates the template_schedule
table if it doesn't already exist, and doesn't touch any existing tables.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_template_schedule'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Check if template_schedule table exists before creating it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'template_schedule' not in existing_tables:
        op.create_table('template_schedule',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('template_id', sa.Integer(), nullable=False),
            sa.Column('day_of_week', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['template_id'], ['workout_template.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        print("[MIGRATION] Created template_schedule table")
    else:
        print("[MIGRATION] template_schedule table already exists, skipping creation")


def downgrade():
    # Only drop if it exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'template_schedule' in existing_tables:
        op.drop_table('template_schedule')
        print("[MIGRATION] Dropped template_schedule table")
    else:
        print("[MIGRATION] template_schedule table doesn't exist, skipping drop")
