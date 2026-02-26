"""Add equipment_type column to exercise, exercise_bank, and template_exercise tables

Revision ID: 007_add_equipment_type
Revises: 006_add_exercise_bank
Create Date: 2026-02-26 00:00:00.000000

Adds an optional equipment_type field (barbell, free_weight, cable, machine) so
equipment can be tracked separately from the exercise name.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_equipment_type'
down_revision = '006_add_exercise_bank'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Add equipment_type to exercise table
    exercise_cols = [c['name'] for c in inspector.get_columns('exercise')]
    if 'equipment_type' not in exercise_cols:
        op.add_column('exercise', sa.Column('equipment_type', sa.String(50), nullable=True))
        print("[MIGRATION] Added equipment_type column to exercise table")
    else:
        print("[MIGRATION] equipment_type already exists on exercise table, skipping")

    # Add equipment_type to exercise_bank table
    bank_cols = [c['name'] for c in inspector.get_columns('exercise_bank')]
    if 'equipment_type' not in bank_cols:
        op.add_column('exercise_bank', sa.Column('equipment_type', sa.String(50), nullable=True))
        print("[MIGRATION] Added equipment_type column to exercise_bank table")
    else:
        print("[MIGRATION] equipment_type already exists on exercise_bank table, skipping")

    # Add equipment_type to template_exercise table
    template_cols = [c['name'] for c in inspector.get_columns('template_exercise')]
    if 'equipment_type' not in template_cols:
        op.add_column('template_exercise', sa.Column('equipment_type', sa.String(50), nullable=True))
        print("[MIGRATION] Added equipment_type column to template_exercise table")
    else:
        print("[MIGRATION] equipment_type already exists on template_exercise table, skipping")


def downgrade():
    op.drop_column('exercise', 'equipment_type')
    op.drop_column('exercise_bank', 'equipment_type')
    op.drop_column('template_exercise', 'equipment_type')
    print("[MIGRATION] Dropped equipment_type columns from exercise, exercise_bank, template_exercise")
