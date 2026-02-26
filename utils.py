"""
Utility functions for GymLog application
"""

import re

# Pre-seeded global exercise bank — names are already normalized (Title Case)
EXERCISE_BANK_SEEDS = [
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
    ("Romanian Deadlift", "Hamstrings"),
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

# Common gym abbreviations and their full forms
ABBREVIATIONS = {
    'db': 'dumbbell',
    'dbs': 'dumbbell',
    'bb': 'barbell',
    'bbs': 'barbell',
    'ez': 'ez bar',
    'ezbar': 'ez bar',
    't-bar': 't-bar',
    'tbar': 't-bar',
    'lat': 'lateral',
    'lats': 'lateral',
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
    'chest fly': 'chest fly',
    'chest press': 'chest press',
    'shoulder press': 'shoulder press',
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

# Equipment type → word mapping (for stripping when equipment_type is tracked separately)
EQUIPMENT_TYPE_WORDS = {
    'barbell':    ['barbell'],
    'free_weight': ['dumbbell'],
    'cable':      ['cable'],
    'machine':    ['machine'],
}

# Equipment words (should come first)
EQUIPMENT_WORDS = [
    'dumbbell', 'barbell', 'cable', 'machine', 'smith', 'smith machine',
    'trap bar', 'ez bar', 't-bar', 'resistance band', 'band', 'kettlebell',
    'bodyweight', 'suspension'
]

# Position/angle words (should come after equipment)
POSITION_WORDS = [
    'incline', 'decline', 'flat', 'seated', 'standing', 'lying', 'kneeling',
    'prone', 'supine', 'bent over', 'single arm', 'single leg', 'unilateral',
    'bilateral', 'alternating', 'close grip', 'wide grip', 'narrow grip',
    'neutral grip', 'overhand', 'underhand', 'hammer', 'reverse'
]

# Movement/exercise type words (should come last)
MOVEMENT_WORDS = [
    'press', 'row', 'curl', 'extension', 'raise', 'fly', 'flye', 'pulldown',
    'pull down', 'pull up', 'chin up', 'push up', 'dip', 'squat', 'lunge',
    'deadlift', 'shrug', 'crunch', 'plank', 'hold', 'walk', 'carry'
]

# Special case patterns for common exercises
SPECIAL_PATTERNS = {
    r'\bbench\s+press\b': 'barbell bench press',
    r'\bsquat\b(?!\s+(rack|stand))': 'barbell squat',
    r'\bdeadlift\b(?!\s+romanian)': 'barbell deadlift',
    r'\boverhead\s+press\b': 'barbell overhead press',
    r'\bmilitary\s+press\b': 'barbell military press',
    r'\bpush\s*ups?\b': 'push up',
    r'\bpull\s*ups?\b': 'pull up',
    r'\bchin\s*ups?\b': 'chin up',
    r'\bdips?\b(?!\s+machine)': 'dip',
    r'\bplank\b': 'plank',
}


def normalize_exercise_name(name, equipment_type=None):
    """
    Normalize exercise name through multiple stages:
    1. Cleaning (trim, lowercase, remove special chars)
    2. Abbreviation expansion
    3. Special pattern matching
    4. Word reordering
    5. Title case formatting

    Args:
        name (str): The exercise name to normalize

    Returns:
        str: The normalized exercise name
    """
    if not name or not name.strip():
        return name

    # Stage 1: Cleaning
    name = name.strip()
    # Remove special characters except spaces, hyphens, and apostrophes
    name = re.sub(r'[^\w\s\-\']', '', name)
    # Convert to lowercase for processing
    name = name.lower()
    # Remove extra spaces
    name = ' '.join(name.split())

    # Stage 2: Apply special patterns first (e.g., "bench press" → "barbell bench press")
    for pattern, replacement in SPECIAL_PATTERNS.items():
        name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)

    # Stage 2b: Strip equipment words when equipment_type is tracked as a separate field
    if equipment_type and equipment_type in EQUIPMENT_TYPE_WORDS:
        for eq_word in EQUIPMENT_TYPE_WORDS[equipment_type]:
            # Remove the equipment word wherever it appears (start, middle, end)
            name = re.sub(rf'\b{re.escape(eq_word)}\b', '', name)
        name = ' '.join(name.split())  # collapse extra spaces

    # Stage 3: Expand abbreviations
    words = name.split()
    expanded_words = []

    i = 0
    while i < len(words):
        word = words[i]

        # Check for multi-word abbreviations (like "leg ext")
        if i < len(words) - 1:
            two_word = f"{word} {words[i+1]}"
            if two_word in ABBREVIATIONS:
                expanded_words.append(ABBREVIATIONS[two_word])
                i += 2
                continue

        # Single word abbreviation
        if word in ABBREVIATIONS:
            expanded_words.append(ABBREVIATIONS[word])
        else:
            expanded_words.append(word)

        i += 1

    name = ' '.join(expanded_words)

    # Stage 4: Word reordering for consistency
    name = reorder_exercise_words(name)

    # Stage 5: Title case and special formatting
    name = name.title()

    # Fix special cases that shouldn't be title-cased normally
    name = name.replace('Ez Bar', 'EZ Bar')
    name = name.replace('T-Bar', 'T-Bar')
    name = re.sub(r'\bDb\b', 'DB', name)
    name = re.sub(r'\bBb\b', 'BB', name)

    # Fix common multi-word terms
    name = re.sub(r'\bRomanian Deadlift\b', 'Romanian Deadlift', name)
    name = re.sub(r'\bSmith Machine\b', 'Smith Machine', name)

    return name


def reorder_exercise_words(name):
    """
    Reorder words in exercise name to follow standard format:
    [Equipment] [Position/Angle] [Muscle/Target] [Movement]

    Examples:
        "press incline dumbbell" → "dumbbell incline press"
        "row cable seated" → "cable seated row"
    """
    words = name.split()

    # Categorize words
    equipment = []
    position = []
    movement = []
    other = []

    # Build multi-word phrases first
    i = 0
    processed_indices = set()

    while i < len(words):
        if i in processed_indices:
            i += 1
            continue

        # Check for multi-word equipment/positions
        if i < len(words) - 1:
            two_word = f"{words[i]} {words[i+1]}"

            if two_word in EQUIPMENT_WORDS:
                equipment.append(two_word)
                processed_indices.add(i)
                processed_indices.add(i+1)
                i += 2
                continue
            elif two_word in POSITION_WORDS:
                position.append(two_word)
                processed_indices.add(i)
                processed_indices.add(i+1)
                i += 2
                continue
            elif two_word in MOVEMENT_WORDS:
                movement.append(two_word)
                processed_indices.add(i)
                processed_indices.add(i+1)
                i += 2
                continue

        # Single word categorization
        word = words[i]
        if word in EQUIPMENT_WORDS:
            equipment.append(word)
            processed_indices.add(i)
        elif word in POSITION_WORDS:
            position.append(word)
            processed_indices.add(i)
        elif word in MOVEMENT_WORDS:
            movement.append(word)
            processed_indices.add(i)
        else:
            other.append(word)
            processed_indices.add(i)

        i += 1

    # Reconstruct in standard order
    result = []
    result.extend(equipment)
    result.extend(position)
    result.extend(other)
    result.extend(movement)

    return ' '.join(result) if result else name


def preview_exercise_normalization(exercise_names):
    """
    Preview what normalization would do to a list of exercise names

    Args:
        exercise_names (list): List of exercise names to preview

    Returns:
        list: List of dicts with 'original', 'normalized', and 'changed' keys
    """
    preview = []

    for name in exercise_names:
        normalized = normalize_exercise_name(name)
        preview.append({
            'original': name,
            'normalized': normalized,
            'changed': name != normalized
        })

    return preview
