"""Add color to WorkoutTemplate and template_id to Workout

Revision ID: 005_add_template_color
Revises: 004_add_workout_draft
Create Date: 2026-01-28 14:00:00.000000

This migration adds:
- color column to workout_template for calendar color coding
- template_id column to workout to track which template was used
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_template_color'
down_revision = '004_add_workout_draft'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Add color to workout_template
    template_columns = [col['name'] for col in inspector.get_columns('workout_template')]
    if 'color' not in template_columns:
        with op.batch_alter_table('workout_template', schema=None) as batch_op:
            batch_op.add_column(sa.Column('color', sa.String(7), nullable=True, server_default='#198754'))
        print("[MIGRATION] Added color column to workout_template table")
    else:
        print("[MIGRATION] color column already exists in workout_template, skipping")

    # Add template_id to workout
    workout_columns = [col['name'] for col in inspector.get_columns('workout')]
    if 'template_id' not in workout_columns:
        with op.batch_alter_table('workout', schema=None) as batch_op:
            batch_op.add_column(sa.Column('template_id', sa.Integer(), nullable=True))
            # Note: SQLite doesn't support adding foreign key constraints to existing tables
            # The FK constraint is defined in the model and will work for new databases
        print("[MIGRATION] Added template_id column to workout table")
    else:
        print("[MIGRATION] template_id column already exists in workout, skipping")


def downgrade():
    with op.batch_alter_table('workout', schema=None) as batch_op:
        batch_op.drop_column('template_id')

    with op.batch_alter_table('workout_template', schema=None) as batch_op:
        batch_op.drop_column('color')

    print("[MIGRATION] Removed color and template_id columns")
