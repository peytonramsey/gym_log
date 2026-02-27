"""Add is_rest_day to workout table

Revision ID: 009_add_rest_day
Revises: 008_add_weekly_goal
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = '009_add_rest_day'
down_revision = '008_add_weekly_goal'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('workout')]
    if 'is_rest_day' not in columns:
        op.add_column('workout', sa.Column('is_rest_day', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('workout', 'is_rest_day')
