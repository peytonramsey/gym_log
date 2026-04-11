"""Normalize exercise names: strip equipment into equipment_type, preserve originals

Revision ID: 011_normalize_exercise_names
Revises: 010_add_iana_timezone
Create Date: 2026-04-11 00:00:00.000000

Changes:
  1. Adds `original_name` column to `exercise` and `template_exercise` (audit trail).
  2. For existing rows where equipment_type IS NULL, detects a known equipment prefix
     in the name, strips it into equipment_type, and saves the bare name.
  3. Re-seeds global ExerciseBank rows (user_id IS NULL) with bare names + equipment_type.

Rows that already have equipment_type set are left unchanged.
Rows with no recognized equipment prefix keep their name as-is (null stays null).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011_normalize_exercise_names'
down_revision = '010_add_iana_timezone'
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Equipment prefix → type mapping.
# Order matters: longer/more-specific prefixes first.
# ---------------------------------------------------------------------------
EQUIPMENT_PREFIXES = [
    # (prefix_lower, equipment_type_value)
    ("smith machine", "machine"),
    ("ez bar",        "barbell"),
    ("trap bar",      "barbell"),
    ("barbell",       "barbell"),
    ("dumbbell",      "free_weight"),
    ("kettlebell",    "free_weight"),
    ("cable",         "cable"),
    ("machine",       "machine"),
]

# Exercises that are inherently bodyweight (no prefix, but known bodyweight)
BODYWEIGHT_NAMES = {
    "pull up", "pull-up", "pullup",
    "chin up", "chin-up", "chinup",
    "push up", "push-up", "pushup",
    "dip", "dips",
    "plank", "side plank",
    "crunch", "decline crunch",
    "hanging leg raise",
    "ab rollout",
    "russian twist",
    "diamond push up",
    "nordic hamstring curl",
    "hyperextension",
    "glute bridge",
    "jump rope",
}


def detect_equipment(name):
    """Return (bare_name, equipment_type) for a given exercise name string."""
    name_lower = name.lower().strip()

    # Check known bodyweight exercises first
    if name_lower in BODYWEIGHT_NAMES:
        return name, "bodyweight"

    # Check equipment prefixes
    for prefix, equip_type in EQUIPMENT_PREFIXES:
        if name_lower.startswith(prefix + " "):
            # Strip the prefix and any leading/trailing whitespace
            bare = name[len(prefix):].strip()
            # Title-case the bare portion (keep any existing mixed case for non-prefix part)
            bare = bare.title()
            return bare, equip_type

    # No prefix found
    return name, None


# ---------------------------------------------------------------------------
# New seed data: (bare_name, muscle_group, equipment_type)
# ---------------------------------------------------------------------------
NEW_SEEDS = [
    # Chest
    ("Bench Press",           "Chest",       "barbell"),
    ("Bench Press",           "Chest",       "free_weight"),
    ("Incline Press",         "Chest",       "barbell"),
    ("Incline Press",         "Chest",       "free_weight"),
    ("Decline Press",         "Chest",       "barbell"),
    ("Decline Press",         "Chest",       "free_weight"),
    ("Fly",                   "Chest",       "cable"),
    ("Fly",                   "Chest",       "free_weight"),
    ("Incline Fly",           "Chest",       "free_weight"),
    ("Pec Deck",              "Chest",       "machine"),
    ("Push Up",               "Chest",       "bodyweight"),
    ("Dip",                   "Chest",       "bodyweight"),
    ("Chest Press",           "Chest",       "machine"),
    # Back
    ("Pull Up",               "Back",        "bodyweight"),
    ("Chin Up",               "Back",        "bodyweight"),
    ("Row",                   "Back",        "barbell"),
    ("Row",                   "Back",        "free_weight"),
    ("Row",                   "Back",        "cable"),
    ("Seated Row",            "Back",        "cable"),
    ("Lat Pulldown",          "Back",        "cable"),
    ("Wide Grip Lat Pulldown","Back",        "cable"),
    ("Close Grip Lat Pulldown","Back",       "cable"),
    ("Face Pull",             "Back",        "cable"),
    ("T-Bar Row",             "Back",        "barbell"),
    ("Deadlift",              "Back",        "barbell"),
    ("Romanian Deadlift",     "Hamstrings",  "barbell"),
    ("Straight Arm Pulldown", "Back",        "cable"),
    ("Hyperextension",        "Back",        "bodyweight"),
    # Shoulders
    ("Overhead Press",        "Shoulders",   "barbell"),
    ("Overhead Press",        "Shoulders",   "free_weight"),
    ("Seated Press",          "Shoulders",   "free_weight"),
    ("Arnold Press",          "Shoulders",   "free_weight"),
    ("Lateral Raise",         "Shoulders",   "free_weight"),
    ("Lateral Raise",         "Shoulders",   "cable"),
    ("Front Raise",           "Shoulders",   "free_weight"),
    ("Rear Delt Fly",         "Shoulders",   "free_weight"),
    ("Rear Delt Fly",         "Shoulders",   "cable"),
    ("Shrug",                 "Shoulders",   "barbell"),
    ("Shrug",                 "Shoulders",   "free_weight"),
    ("Upright Row",           "Shoulders",   "barbell"),
    # Biceps
    ("Curl",                  "Biceps",      "barbell"),
    ("Curl",                  "Biceps",      "free_weight"),
    ("Incline Curl",          "Biceps",      "free_weight"),
    ("Hammer Curl",           "Biceps",      "free_weight"),
    ("Preacher Curl",         "Biceps",      "barbell"),
    ("Curl",                  "Biceps",      "cable"),
    ("EZ Bar Curl",           "Biceps",      "barbell"),
    ("Concentration Curl",    "Biceps",      "free_weight"),
    # Triceps
    ("Tricep Pushdown",       "Triceps",     "cable"),
    ("Overhead Tricep Extension", "Triceps", "cable"),
    ("Skull Crusher",         "Triceps",     "barbell"),
    ("Close Grip Bench Press","Triceps",     "barbell"),
    ("Tricep Kickback",       "Triceps",     "free_weight"),
    ("Diamond Push Up",       "Triceps",     "bodyweight"),
    # Quads
    ("Squat",                 "Quads",       "barbell"),
    ("Front Squat",           "Quads",       "barbell"),
    ("Leg Press",             "Quads",       "machine"),
    ("Hack Squat",            "Quads",       "machine"),
    ("Leg Extension",         "Quads",       "machine"),
    ("Lunge",                 "Quads",       "free_weight"),
    ("Lunge",                 "Quads",       "barbell"),
    ("Bulgarian Split Squat", "Quads",       "free_weight"),
    ("Squat",                 "Quads",       "machine"),       # smith machine
    # Hamstrings
    ("Lying Leg Curl",        "Hamstrings",  "machine"),
    ("Seated Leg Curl",       "Hamstrings",  "machine"),
    ("Stiff Leg Deadlift",    "Hamstrings",  "barbell"),
    ("Nordic Hamstring Curl", "Hamstrings",  "bodyweight"),
    # Glutes
    ("Hip Thrust",            "Glutes",      "bodyweight"),
    ("Hip Thrust",            "Glutes",      "barbell"),
    ("Kickback",              "Glutes",      "cable"),
    ("Glute Bridge",          "Glutes",      "bodyweight"),
    # Calves
    ("Calf Raise",            "Calves",      "machine"),       # standing machine
    ("Seated Calf Raise",     "Calves",      "machine"),
    ("Leg Press Calf Raise",  "Calves",      "machine"),
    ("Calf Raise",            "Calves",      "barbell"),       # standing barbell
    # Core
    ("Plank",                 "Core",        "bodyweight"),
    ("Crunch",                "Core",        "bodyweight"),
    ("Crunch",                "Core",        "cable"),
    ("Hanging Leg Raise",     "Core",        "bodyweight"),
    ("Ab Rollout",            "Core",        "bodyweight"),
    ("Russian Twist",         "Core",        "bodyweight"),
    ("Side Plank",            "Core",        "bodyweight"),
    ("Decline Crunch",        "Core",        "bodyweight"),
    # Cardio
    ("Treadmill Run",         "Cardio",      None),
    ("Stationary Bike",       "Cardio",      None),
    ("Rowing Machine",        "Cardio",      None),
    ("Jump Rope",             "Cardio",      "bodyweight"),
    ("Stair Climber",         "Cardio",      None),
]


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # ------------------------------------------------------------------
    # 1. Add original_name columns
    # ------------------------------------------------------------------
    exercise_cols = [c['name'] for c in inspector.get_columns('exercise')]
    if 'original_name' not in exercise_cols:
        op.add_column('exercise', sa.Column('original_name', sa.String(100), nullable=True))
        print("[MIGRATION] Added original_name column to exercise table")

    template_cols = [c['name'] for c in inspector.get_columns('template_exercise')]
    if 'original_name' not in template_cols:
        op.add_column('template_exercise', sa.Column('original_name', sa.String(100), nullable=True))
        print("[MIGRATION] Added original_name column to template_exercise table")

    # ------------------------------------------------------------------
    # 2. Normalize existing Exercise rows (equipment_type IS NULL only)
    # ------------------------------------------------------------------
    exercise_table = sa.table(
        'exercise',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('original_name', sa.String),
        sa.column('equipment_type', sa.String),
    )
    rows = conn.execute(
        sa.select(exercise_table.c.id, exercise_table.c.name)
        .where(exercise_table.c.equipment_type.is_(None))
    ).fetchall()

    updated_exercise = 0
    for row_id, name in rows:
        bare, equip = detect_equipment(name)
        # Always save original_name
        update_vals = {'original_name': name}
        if equip is not None:
            update_vals['name'] = bare
            update_vals['equipment_type'] = equip
        conn.execute(
            exercise_table.update()
            .where(exercise_table.c.id == row_id)
            .values(**update_vals)
        )
        if equip is not None:
            updated_exercise += 1

    print(f"[MIGRATION] Normalized {updated_exercise}/{len(rows)} exercise rows "
          f"(original_name preserved for all {len(rows)})")

    # ------------------------------------------------------------------
    # 3. Normalize existing TemplateExercise rows (equipment_type IS NULL only)
    # ------------------------------------------------------------------
    template_exercise_table = sa.table(
        'template_exercise',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('original_name', sa.String),
        sa.column('equipment_type', sa.String),
    )
    t_rows = conn.execute(
        sa.select(template_exercise_table.c.id, template_exercise_table.c.name)
        .where(template_exercise_table.c.equipment_type.is_(None))
    ).fetchall()

    updated_template = 0
    for row_id, name in t_rows:
        bare, equip = detect_equipment(name)
        update_vals = {'original_name': name}
        if equip is not None:
            update_vals['name'] = bare
            update_vals['equipment_type'] = equip
        conn.execute(
            template_exercise_table.update()
            .where(template_exercise_table.c.id == row_id)
            .values(**update_vals)
        )
        if equip is not None:
            updated_template += 1

    print(f"[MIGRATION] Normalized {updated_template}/{len(t_rows)} template_exercise rows")

    # ------------------------------------------------------------------
    # 4. Re-seed ExerciseBank: delete old global seeds, insert new ones
    # ------------------------------------------------------------------
    bank_table = sa.table(
        'exercise_bank',
        sa.column('id', sa.Integer),
        sa.column('user_id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('muscle_group', sa.String),
        sa.column('equipment_type', sa.String),
        sa.column('is_custom', sa.Boolean),
    )

    # Delete all existing global seeds (user_id IS NULL)
    deleted = conn.execute(
        bank_table.delete().where(bank_table.c.user_id.is_(None))
    )
    print(f"[MIGRATION] Removed {deleted.rowcount} old global ExerciseBank seeds")

    # Insert new seeds
    op.bulk_insert(bank_table, [
        {
            'user_id': None,
            'name': name,
            'muscle_group': muscle_group,
            'equipment_type': equipment_type,
            'is_custom': False,
        }
        for name, muscle_group, equipment_type in NEW_SEEDS
    ])
    print(f"[MIGRATION] Inserted {len(NEW_SEEDS)} new global ExerciseBank seeds")


def downgrade():
    """Remove original_name columns. Data migration is irreversible."""
    op.drop_column('exercise', 'original_name')
    op.drop_column('template_exercise', 'original_name')
    print("[MIGRATION] Dropped original_name columns (exercise name migration is NOT reversed)")
