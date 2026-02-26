"""Add exercise_bank table with global seed exercises

Revision ID: 006_add_exercise_bank
Revises: a1c2a64860b4
Create Date: 2026-02-26 00:00:00.000000

Creates a new exercise_bank table for the Exercise Bank feature.
Global exercises (user_id=NULL) are seeded on migration.
Users can add their own custom exercises (user_id set, is_custom=True).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_exercise_bank'
down_revision = 'a1c2a64860b4'
branch_labels = None
depends_on = None

SEEDS = [
    # Chest
    ("Barbell Bench Press", "Chest"),
    ("Dumbbell Bench Press", "Chest"),
    ("Incline Barbell Press", "Chest"),
    ("Incline Dumbbell Press", "Chest"),
    ("Decline Barbell Press", "Chest"),
    ("Decline Dumbbell Press", "Chest"),
    ("Cable Fly", "Chest"),
    ("Dumbbell Fly", "Chest"),
    ("Incline Dumbbell Fly", "Chest"),
    ("Pec Deck", "Chest"),
    ("Push Up", "Chest"),
    ("Dip", "Chest"),
    ("Chest Press Machine", "Chest"),
    # Back
    ("Pull Up", "Back"),
    ("Chin Up", "Back"),
    ("Barbell Row", "Back"),
    ("Dumbbell Row", "Back"),
    ("Cable Row", "Back"),
    ("Seated Cable Row", "Back"),
    ("Lat Pulldown", "Back"),
    ("Wide Grip Lat Pulldown", "Back"),
    ("Close Grip Lat Pulldown", "Back"),
    ("Face Pull", "Back"),
    ("T-Bar Row", "Back"),
    ("Barbell Deadlift", "Back"),
    ("Romanian Deadlift", "Back"),
    ("Straight Arm Pulldown", "Back"),
    ("Hyperextension", "Back"),
    # Shoulders
    ("Barbell Overhead Press", "Shoulders"),
    ("Dumbbell Overhead Press", "Shoulders"),
    ("Seated Dumbbell Press", "Shoulders"),
    ("Arnold Press", "Shoulders"),
    ("Dumbbell Lateral Raise", "Shoulders"),
    ("Cable Lateral Raise", "Shoulders"),
    ("Dumbbell Front Raise", "Shoulders"),
    ("Rear Delt Fly", "Shoulders"),
    ("Cable Rear Delt Fly", "Shoulders"),
    ("Barbell Shrug", "Shoulders"),
    ("Dumbbell Shrug", "Shoulders"),
    ("Upright Row", "Shoulders"),
    # Biceps
    ("Barbell Curl", "Biceps"),
    ("Dumbbell Curl", "Biceps"),
    ("Incline Dumbbell Curl", "Biceps"),
    ("Hammer Curl", "Biceps"),
    ("Preacher Curl", "Biceps"),
    ("Cable Curl", "Biceps"),
    ("EZ Bar Curl", "Biceps"),
    ("Concentration Curl", "Biceps"),
    # Triceps
    ("Tricep Pushdown", "Triceps"),
    ("Overhead Tricep Extension", "Triceps"),
    ("Skull Crusher", "Triceps"),
    ("Close Grip Bench Press", "Triceps"),
    ("Tricep Kickback", "Triceps"),
    ("Cable Overhead Tricep Extension", "Triceps"),
    ("Diamond Push Up", "Triceps"),
    # Quads
    ("Barbell Squat", "Quads"),
    ("Front Squat", "Quads"),
    ("Leg Press", "Quads"),
    ("Hack Squat", "Quads"),
    ("Leg Extension", "Quads"),
    ("Dumbbell Lunge", "Quads"),
    ("Barbell Lunge", "Quads"),
    ("Bulgarian Split Squat", "Quads"),
    ("Smith Machine Squat", "Quads"),
    # Hamstrings
    ("Lying Leg Curl", "Hamstrings"),
    ("Seated Leg Curl", "Hamstrings"),
    ("Stiff Leg Deadlift", "Hamstrings"),
    ("Nordic Hamstring Curl", "Hamstrings"),
    # Glutes
    ("Hip Thrust", "Glutes"),
    ("Barbell Hip Thrust", "Glutes"),
    ("Cable Kickback", "Glutes"),
    ("Glute Bridge", "Glutes"),
    # Calves
    ("Standing Calf Raise", "Calves"),
    ("Seated Calf Raise", "Calves"),
    ("Leg Press Calf Raise", "Calves"),
    # Core
    ("Plank", "Core"),
    ("Crunch", "Core"),
    ("Cable Crunch", "Core"),
    ("Hanging Leg Raise", "Core"),
    ("Ab Rollout", "Core"),
    ("Russian Twist", "Core"),
    ("Side Plank", "Core"),
    ("Decline Crunch", "Core"),
    # Cardio
    ("Treadmill Run", "Cardio"),
    ("Stationary Bike", "Cardio"),
    ("Rowing Machine", "Cardio"),
    ("Jump Rope", "Cardio"),
    ("Stair Climber", "Cardio"),
]


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'exercise_bank' not in inspector.get_table_names():
        op.create_table(
            'exercise_bank',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('muscle_group', sa.String(50), nullable=True),
            sa.Column('is_custom', sa.Boolean(), nullable=False, server_default='0'),
            sa.PrimaryKeyConstraint('id'),
        )
        print("[MIGRATION] Created exercise_bank table")

        # Seed global exercises
        exercise_bank_table = sa.table(
            'exercise_bank',
            sa.column('user_id', sa.Integer),
            sa.column('name', sa.String),
            sa.column('muscle_group', sa.String),
            sa.column('is_custom', sa.Boolean),
        )
        op.bulk_insert(exercise_bank_table, [
            {'user_id': None, 'name': name, 'muscle_group': group, 'is_custom': False}
            for name, group in SEEDS
        ])
        print(f"[MIGRATION] Seeded {len(SEEDS)} global exercises into exercise_bank")
    else:
        print("[MIGRATION] exercise_bank table already exists, skipping")


def downgrade():
    op.drop_table('exercise_bank')
    print("[MIGRATION] Dropped exercise_bank table")
