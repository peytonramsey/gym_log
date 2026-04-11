"""
Utility functions for GymLog application
"""

import re

# ---------------------------------------------------------------------------
# Pre-seeded global exercise bank — 3-tuple: (bare_name, muscle_group, equipment_type)
# Names are already bare (no equipment word). Equipment type is explicit.
# ---------------------------------------------------------------------------
EXERCISE_BANK_SEEDS = [
    # Chest
    ("Bench Press",            "Chest",       "barbell"),
    ("Bench Press",            "Chest",       "free_weight"),
    ("Incline Press",          "Chest",       "barbell"),
    ("Incline Press",          "Chest",       "free_weight"),
    ("Decline Press",          "Chest",       "barbell"),
    ("Decline Press",          "Chest",       "free_weight"),
    ("Fly",                    "Chest",       "cable"),
    ("Fly",                    "Chest",       "free_weight"),
    ("Incline Fly",            "Chest",       "free_weight"),
    ("Pec Deck",               "Chest",       "machine"),
    ("Push Up",                "Chest",       "bodyweight"),
    ("Dip",                    "Chest",       "bodyweight"),
    ("Chest Press",            "Chest",       "machine"),
    # Back
    ("Pull Up",                "Back",        "bodyweight"),
    ("Chin Up",                "Back",        "bodyweight"),
    ("Row",                    "Back",        "barbell"),
    ("Row",                    "Back",        "free_weight"),
    ("Row",                    "Back",        "cable"),
    ("Seated Row",             "Back",        "cable"),
    ("Lat Pulldown",           "Back",        "cable"),
    ("Wide Grip Lat Pulldown", "Back",        "cable"),
    ("Close Grip Lat Pulldown","Back",        "cable"),
    ("Face Pull",              "Back",        "cable"),
    ("T-Bar Row",              "Back",        "barbell"),
    ("Deadlift",               "Back",        "barbell"),
    ("Straight Arm Pulldown",  "Back",        "cable"),
    ("Hyperextension",         "Back",        "bodyweight"),
    # Shoulders
    ("Overhead Press",         "Shoulders",   "barbell"),
    ("Overhead Press",         "Shoulders",   "free_weight"),
    ("Seated Press",           "Shoulders",   "free_weight"),
    ("Arnold Press",           "Shoulders",   "free_weight"),
    ("Lateral Raise",          "Shoulders",   "free_weight"),
    ("Lateral Raise",          "Shoulders",   "cable"),
    ("Front Raise",            "Shoulders",   "free_weight"),
    ("Rear Delt Fly",          "Shoulders",   "free_weight"),
    ("Rear Delt Fly",          "Shoulders",   "cable"),
    ("Shrug",                  "Shoulders",   "barbell"),
    ("Shrug",                  "Shoulders",   "free_weight"),
    ("Upright Row",            "Shoulders",   "barbell"),
    # Biceps
    ("Curl",                   "Biceps",      "barbell"),
    ("Curl",                   "Biceps",      "free_weight"),
    ("Incline Curl",           "Biceps",      "free_weight"),
    ("Hammer Curl",            "Biceps",      "free_weight"),
    ("Preacher Curl",          "Biceps",      "barbell"),
    ("Curl",                   "Biceps",      "cable"),
    ("EZ Bar Curl",            "Biceps",      "barbell"),
    ("Concentration Curl",     "Biceps",      "free_weight"),
    # Triceps
    ("Tricep Pushdown",        "Triceps",     "cable"),
    ("Overhead Tricep Extension", "Triceps",  "cable"),
    ("Skull Crusher",          "Triceps",     "barbell"),
    ("Close Grip Bench Press", "Triceps",     "barbell"),
    ("Tricep Kickback",        "Triceps",     "free_weight"),
    ("Diamond Push Up",        "Triceps",     "bodyweight"),
    # Quads
    ("Squat",                  "Quads",       "barbell"),
    ("Front Squat",            "Quads",       "barbell"),
    ("Leg Press",              "Quads",       "machine"),
    ("Hack Squat",             "Quads",       "machine"),
    ("Leg Extension",          "Quads",       "machine"),
    ("Lunge",                  "Quads",       "free_weight"),
    ("Lunge",                  "Quads",       "barbell"),
    ("Bulgarian Split Squat",  "Quads",       "free_weight"),
    ("Squat",                  "Quads",       "machine"),     # smith machine squat
    # Hamstrings
    ("Romanian Deadlift",      "Hamstrings",  "barbell"),
    ("Lying Leg Curl",         "Hamstrings",  "machine"),
    ("Seated Leg Curl",        "Hamstrings",  "machine"),
    ("Stiff Leg Deadlift",     "Hamstrings",  "barbell"),
    ("Nordic Hamstring Curl",  "Hamstrings",  "bodyweight"),
    # Glutes
    ("Hip Thrust",             "Glutes",      "bodyweight"),
    ("Hip Thrust",             "Glutes",      "barbell"),
    ("Kickback",               "Glutes",      "cable"),
    ("Glute Bridge",           "Glutes",      "bodyweight"),
    # Calves
    ("Calf Raise",             "Calves",      "machine"),
    ("Seated Calf Raise",      "Calves",      "machine"),
    ("Leg Press Calf Raise",   "Calves",      "machine"),
    ("Calf Raise",             "Calves",      "barbell"),
    # Core
    ("Plank",                  "Core",        "bodyweight"),
    ("Crunch",                 "Core",        "bodyweight"),
    ("Crunch",                 "Core",        "cable"),
    ("Hanging Leg Raise",      "Core",        "bodyweight"),
    ("Ab Rollout",             "Core",        "bodyweight"),
    ("Russian Twist",          "Core",        "bodyweight"),
    ("Side Plank",             "Core",        "bodyweight"),
    ("Decline Crunch",         "Core",        "bodyweight"),
    # Cardio
    ("Treadmill Run",          "Cardio",      None),
    ("Stationary Bike",        "Cardio",      None),
    ("Rowing Machine",         "Cardio",      None),
    ("Jump Rope",              "Cardio",      "bodyweight"),
    ("Stair Climber",          "Cardio",      None),
]

# ---------------------------------------------------------------------------
# Common gym abbreviations → full forms
# ---------------------------------------------------------------------------
ABBREVIATIONS = {
    'db': 'dumbbell',
    'dbs': 'dumbbell',
    'bb': 'barbell',
    'bbs': 'barbell',
    'kb': 'kettlebell',
    'kbs': 'kettlebell',
    'ez': 'ez bar',
    'ezbar': 'ez bar',
    't-bar': 't-bar',
    'tbar': 't-bar',
    # Note: 'lat'/'lats' intentionally NOT here — in gym context 'lat' means
    # latissimus dorsi (the muscle), NOT 'lateral'. 'Lat Pulldown' must stay
    # 'Lat Pulldown', not become 'Lateral Pulldown'.
    'inc': 'incline',
    'incl': 'incline',
    'dec': 'decline',
    'decl': 'decline',
    'ext': 'extension',
    'rdl': 'romanian deadlift',
    'rdls': 'romanian deadlift',
    'ohp': 'overhead press',
    'btn': 'behind the neck',
    'cg': 'close grip',
    'wg': 'wide grip',
    'ng': 'narrow grip',
    'ss': 'single arm',
    'sa': 'single arm',
    'leg ext': 'leg extension',
    'leg curl': 'leg curl',
    'ham curl': 'hamstring curl',
    'calf raise': 'calf raise',
    'leg press': 'leg press',
    'pec deck': 'pec deck',
    'pec fly': 'pec fly',
    'chest fly': 'fly',
    'chest press': 'chest press',
    'shoulder press': 'overhead press',
    'front raise': 'front raise',
    'side raise': 'lateral raise',
    'rear delt': 'rear delt',
    'face pull': 'face pull',
    'pull down': 'pulldown',
    'pulldown': 'pulldown',
    'pull up': 'pull up',
    'chin up': 'chin up',
    'push up': 'push up',
}

# ---------------------------------------------------------------------------
# Equipment type → words to strip from the exercise name.
# When equipment_type is tracked as a separate field, these words are redundant
# in the name and should be removed.
# Order within each list matters: longer/more-specific first.
# ---------------------------------------------------------------------------
EQUIPMENT_TYPE_WORDS = {
    'barbell':    ['ez bar', 'trap bar', 'barbell'],
    'free_weight': ['kettlebell', 'dumbbell'],
    'cable':      ['cable'],
    'machine':    ['smith machine', 'smith', 'machine'],
    'bodyweight': [],  # bodyweight names are already bare
}

# ---------------------------------------------------------------------------
# Position/angle words for reordering (no equipment — equipment is gone by now)
# ---------------------------------------------------------------------------
POSITION_WORDS = [
    'incline', 'decline', 'flat', 'seated', 'standing', 'lying', 'kneeling',
    'prone', 'supine', 'bent over', 'single arm', 'single leg', 'unilateral',
    'bilateral', 'alternating', 'close grip', 'wide grip', 'narrow grip',
    'neutral grip', 'overhand', 'underhand', 'hammer', 'reverse',
]

# Movement/exercise type words
MOVEMENT_WORDS = [
    'press', 'row', 'curl', 'extension', 'raise', 'fly', 'flye', 'pulldown',
    'pull down', 'pull up', 'chin up', 'push up', 'dip', 'squat', 'lunge',
    'deadlift', 'shrug', 'crunch', 'plank', 'hold', 'walk', 'carry', 'thrust',
    'kickback', 'pushdown',
]


def normalize_exercise_name(name, equipment_type=None):
    """
    Normalize an exercise name to canonical bare form.

    Pipeline:
      1. Clean (trim, remove special chars, lowercase)
      2. Expand abbreviations
      3. Strip equipment words matching equipment_type (if provided)
      4. Reorder words: [Position] [Target] [Movement]
      5. Title case + special-case fixes

    Args:
        name (str): Raw exercise name entered by user.
        equipment_type (str | None): One of barbell, free_weight, cable,
            machine, bodyweight, or None (untagged).

    Returns:
        str: Canonical bare name in Title Case.
    """
    if not name or not name.strip():
        return name

    # Stage 1: Clean
    name = name.strip()
    name = re.sub(r'[^\w\s\-\']', '', name)
    name = name.lower()
    name = ' '.join(name.split())

    # Stage 2: Expand abbreviations
    words = name.split()
    expanded = []
    i = 0
    while i < len(words):
        # Try 2-word abbreviation first
        if i < len(words) - 1:
            two_word = f"{words[i]} {words[i+1]}"
            if two_word in ABBREVIATIONS:
                expanded.append(ABBREVIATIONS[two_word])
                i += 2
                continue
        # Single-word abbreviation
        if words[i] in ABBREVIATIONS:
            expanded.append(ABBREVIATIONS[words[i]])
        else:
            expanded.append(words[i])
        i += 1
    name = ' '.join(expanded)

    # Stage 3: Strip equipment words for the declared equipment_type
    if equipment_type and equipment_type in EQUIPMENT_TYPE_WORDS:
        for eq_word in EQUIPMENT_TYPE_WORDS[equipment_type]:
            # Remove the equipment word wherever it appears (start, middle, end)
            name = re.sub(rf'\b{re.escape(eq_word)}\b', '', name, flags=re.IGNORECASE)
        name = ' '.join(name.split())  # collapse extra spaces

    # Stage 4: Reorder words to [Position] [Target] [Movement]
    name = reorder_exercise_words(name)

    # Stage 5: Title case + special-case fixes
    name = name.title()
    name = name.replace('Ez Bar', 'EZ Bar')
    name = name.replace('T-Bar', 'T-Bar')
    name = re.sub(r'\bDb\b', 'DB', name)
    name = re.sub(r'\bBb\b', 'BB', name)
    name = re.sub(r'\bRomanian Deadlift\b', 'Romanian Deadlift', name)

    return name


def reorder_exercise_words(name):
    """
    Reorder words in an exercise name to follow the standard bare-name format:
    [Position/Angle] [Target/Qualifier] [Movement]

    Examples:
        "incline press" → "incline press"  (already correct)
        "press incline" → "incline press"
        "row seated cable" → "seated row"  (cable already stripped upstream)
    """
    words = name.split()
    if not words:
        return name

    position = []
    movement = []
    other = []
    processed = set()

    i = 0
    while i < len(words):
        if i in processed:
            i += 1
            continue

        # Check 2-word phrases
        if i < len(words) - 1:
            two_word = f"{words[i]} {words[i+1]}"
            if two_word in POSITION_WORDS:
                position.append(two_word)
                processed.add(i)
                processed.add(i + 1)
                i += 2
                continue
            if two_word in MOVEMENT_WORDS:
                movement.append(two_word)
                processed.add(i)
                processed.add(i + 1)
                i += 2
                continue

        word = words[i]
        if word in POSITION_WORDS:
            position.append(word)
            processed.add(i)
        elif word in MOVEMENT_WORDS:
            movement.append(word)
            processed.add(i)
        else:
            other.append(word)
            processed.add(i)

        i += 1

    result = position + other + movement
    return ' '.join(result) if result else name


def preview_exercise_normalization(exercise_records):
    """
    Preview what normalization would do to a list of (name, equipment_type) records.

    Args:
        exercise_records (list): List of dicts with 'name' and 'equipment_type' keys.

    Returns:
        list: List of dicts with 'original', 'normalized', 'equipment_type', 'changed'.
    """
    preview = []
    for rec in exercise_records:
        name = rec.get('name', '')
        equip = rec.get('equipment_type')
        normalized = normalize_exercise_name(name, equip)
        preview.append({
            'original': name,
            'normalized': normalized,
            'equipment_type': equip,
            'changed': name != normalized,
        })
    return preview
