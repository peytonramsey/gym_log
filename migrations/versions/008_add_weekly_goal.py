"""Add weekly_goal to users table

Revision ID: 008_add_weekly_goal
Revises: 007_add_equipment_type
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = '008_add_weekly_goal'
down_revision = '007_add_equipment_type'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('users')]
    if 'weekly_goal' not in columns:
        op.add_column('users', sa.Column('weekly_goal', sa.Integer(), nullable=True, server_default='3'))


def downgrade():
    op.drop_column('users', 'weekly_goal')
