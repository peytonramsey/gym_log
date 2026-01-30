from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from models import db, User, Workout, Exercise, BodyMetrics, Meal, FoodItem, NutritionGoals, Supplement, WorkoutTemplate, TemplateExercise, TemplateSchedule
from datetime import datetime, timedelta
from sqlalchemy import func
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# App version
VERSION = "1.0.4"

# Unit conversion factors to grams/ml
UNIT_CONVERSIONS = {
    'g': 1.0,
    'kg': 1000.0,
    'oz': 28.3495,
    'lb': 453.592,
    'ml': 1.0,
    'l': 1000.0,
    'fl oz': 29.5735,
    'cup': 240.0,
    'tbsp': 15.0,
    'tsp': 5.0,
    'serving': 1.0  # Will be handled specially
}

def convert_to_base_unit(quantity, unit):
    """Convert any unit to grams or ml (base unit)"""
    if unit in UNIT_CONVERSIONS:
        return quantity * UNIT_CONVERSIONS[unit]
    return quantity  # Default to grams if unknown

app = Flask(__name__)

# Database configuration - use PostgreSQL in production, SQLite in development
database_url = os.getenv('DATABASE_URL', 'sqlite:///gymlog.db')

# Render uses 'postgres://' but SQLAlchemy needs 'postgresql://'
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Session configuration for persistent login
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)  # Remember me for 30 days
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # Session lifetime
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

db.init_app(app)

# Initialize Flask-Migrate for database migrations
migrate = Migrate(app, db)

def cleanup_old_drafts():
    """Delete draft workouts older than 24 hours"""
    try:
        cutoff = datetime.now() - timedelta(hours=24)
        old_drafts = Workout.query.filter(
            Workout.is_draft == True,
            Workout.date < cutoff
        ).all()

        for draft in old_drafts:
            db.session.delete(draft)

        if old_drafts:
            db.session.commit()
            print(f"[CLEANUP] Deleted {len(old_drafts)} old draft workouts")
    except Exception as e:
        # Column may not exist yet if migration hasn't run
        print(f"[CLEANUP] Skipped draft cleanup (migration may be pending): {e}")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_admin_user():
    """Create admin user if it doesn't exist"""
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@fitglyph.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

    # Check if admin user already exists
    existing_admin = User.query.filter_by(username=admin_username).first()

    if not existing_admin:
        # Create admin user
        admin = User(username=admin_username, email=admin_email)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"[SUCCESS] Admin user '{admin_username}' created successfully!")
    else:
        print(f"[INFO] Admin user '{admin_username}' already exists.")


def populate_demo_data(user):
    """Populate demo user with realistic fitness data"""
    # Clear existing data for demo user
    Workout.query.filter_by(user_id=user.id).delete()
    BodyMetrics.query.filter_by(user_id=user.id).delete()
    Meal.query.filter_by(user_id=user.id).delete()
    NutritionGoals.query.filter_by(user_id=user.id).delete()
    Supplement.query.filter_by(user_id=user.id).delete()
    WorkoutTemplate.query.filter_by(user_id=user.id).delete()
    WeightPrediction.query.filter_by(user_id=user.id).delete()

    # Create nutrition goals
    nutrition_goals = NutritionGoals(
        user_id=user.id,
        calories_goal=2500,
        protein_goal=180,
        carbs_goal=250,
        fats_goal=80,
        is_active=True
    )
    db.session.add(nutrition_goals)

    # Create body metrics history (last 90 days)
    base_weight = 180.0
    for i in range(90, 0, -7):  # Weekly measurements
        date = (datetime.now() - timedelta(days=i)).replace(hour=8, minute=0, second=0, microsecond=0)
        weight_variation = (90 - i) * 0.05  # Gradual weight gain
        metrics = BodyMetrics(
            user_id=user.id,
            date=date,
            weight=round(base_weight + weight_variation, 1)
        )
        db.session.add(metrics)

    # Create workout history (last 30 days, 4x per week)
    workout_types = [
        ('Push Day', [
            ('Bench Press', 4, [8, 8, 6, 6], [185, 185, 205, 205]),
            ('Incline Dumbbell Press', 4, [10, 10, 8, 8], [70, 70, 75, 75]),
            ('Overhead Press', 3, [8, 8, 8], [115, 115, 115]),
            ('Tricep Pushdowns', 3, [12, 12, 12], [50, 50, 50]),
            ('Lateral Raises', 3, [15, 15, 15], [20, 20, 20])
        ]),
        ('Pull Day', [
            ('Deadlift', 4, [5, 5, 3, 3], [275, 275, 315, 315]),
            ('Pull-ups', 4, [10, 8, 8, 6], [0, 0, 0, 0]),
            ('Barbell Rows', 4, [8, 8, 8, 8], [185, 185, 185, 185]),
            ('Face Pulls', 3, [15, 15, 15], [40, 40, 40]),
            ('Hammer Curls', 3, [12, 12, 12], [35, 35, 35])
        ]),
        ('Leg Day', [
            ('Squats', 4, [8, 8, 6, 6], [225, 225, 245, 245]),
            ('Romanian Deadlifts', 4, [10, 10, 10, 10], [185, 185, 185, 185]),
            ('Leg Press', 3, [12, 12, 12], [360, 360, 360]),
            ('Leg Curls', 3, [12, 12, 12], [90, 90, 90]),
            ('Calf Raises', 4, [15, 15, 15, 15], [135, 135, 135, 135])
        ]),
        ('Upper Body', [
            ('Bench Press', 3, [10, 10, 10], [165, 165, 165]),
            ('Lat Pulldowns', 3, [10, 10, 10], [140, 140, 140]),
            ('Dumbbell Rows', 3, [12, 12, 12], [65, 65, 65]),
            ('Dumbbell Flyes', 3, [12, 12, 12], [30, 30, 30]),
            ('Cable Curls', 3, [15, 15, 15], [40, 40, 40])
        ])
    ]

    # Create workouts aligned with scheduled days for consistency tracking
    # Schedule: Monday (0), Tuesday (1), Thursday (3), Saturday (5)
    scheduled_days = [0, 1, 3, 5]  # Maps to workout_types indices

    # Create workouts for the last 4 weeks on the scheduled days
    for week in range(4):
        # Start from 4 weeks ago
        week_start = datetime.now() - timedelta(weeks=4-week)
        # Find the Monday of that week
        days_since_monday = week_start.weekday()
        monday = week_start - timedelta(days=days_since_monday)

        for day_of_week in scheduled_days:
            workout_date = (monday + timedelta(days=day_of_week)).replace(hour=10, minute=0, second=0, microsecond=0)

            # Only create if date is in the past
            if workout_date.date() <= datetime.now().date():
                workout_type_idx = scheduled_days.index(day_of_week)
                workout_name, exercises = workout_types[workout_type_idx]

                workout = Workout(
                    user_id=user.id,
                    date=workout_date,
                    notes=f"{workout_name} - Great session! Felt strong today."
                )
                db.session.add(workout)
                db.session.flush()

                for ex_name, num_sets, reps, weights in exercises:
                    for set_num in range(num_sets):
                        exercise = Exercise(
                            workout_id=workout.id,
                            name=ex_name,
                            sets=1,
                            reps=reps[set_num] if set_num < len(reps) else reps[-1],
                            weight=weights[set_num] if set_num < len(weights) else weights[-1]
                        )
                        db.session.add(exercise)

    # Create nutrition logs (last 7 days) with realistic values
    meal_templates = {
        'Breakfast': [
            ('Scrambled Eggs (3 large)', 210, 18, 2, 15),
            ('Whole Wheat Toast (2 slices)', 140, 6, 24, 2),
            ('Avocado (1/2)', 120, 1, 6, 11),
            ('Greek Yogurt (1 cup)', 150, 17, 8, 4)
        ],
        'Lunch': [
            ('Grilled Chicken Breast (6oz)', 280, 53, 0, 6),
            ('Brown Rice (1 cup cooked)', 215, 5, 45, 2),
            ('Broccoli (1 cup)', 55, 4, 11, 0),
            ('Olive Oil (1 tbsp)', 120, 0, 0, 14)
        ],
        'Dinner': [
            ('Salmon Fillet (6oz)', 350, 39, 0, 21),
            ('Sweet Potato (1 medium)', 103, 2, 24, 0),
            ('Green Beans (1 cup)', 44, 2, 10, 0),
            ('Quinoa (1/2 cup cooked)', 111, 4, 20, 2)
        ],
        'Snack': [
            ('Protein Shake', 160, 30, 5, 3),
            ('Banana', 105, 1, 27, 0),
            ('Almonds (1 oz)', 164, 6, 6, 14)
        ]
    }

    for days_ago in range(7):
        # Create a date for each day (not datetime to avoid time issues)
        meal_date = (datetime.now() - timedelta(days=days_ago)).replace(hour=12, minute=0, second=0, microsecond=0)

        for meal_type, foods in meal_templates.items():
            meal = Meal(
                user_id=user.id,
                date=meal_date,
                meal_type=meal_type,
                notes=''
            )
            db.session.add(meal)
            db.session.flush()

            for food_name, cals, protein, carbs, fats in foods:
                food_item = FoodItem(
                    meal_id=meal.id,
                    name=food_name,
                    serving_size='1 serving',
                    quantity=1.0,
                    unit='serving',
                    calories=cals,
                    protein=protein,
                    carbs=carbs,
                    fats=fats
                )
                db.session.add(food_item)

    # Create supplements log (last 7 days)
    supplements_daily = [
        ('Whey Protein', '30g', 'Morning'),
        ('Creatine Monohydrate', '5g', 'Pre-Workout'),
        ('Multivitamin', '1 tablet', 'Morning'),
        ('Fish Oil', '2 capsules', 'Evening'),
        ('Vitamin D3', '5000 IU', 'Morning')
    ]

    for days_ago in range(7):
        supp_date = (datetime.now() - timedelta(days=days_ago)).replace(hour=12, minute=0, second=0, microsecond=0)
        for supp_name, dosage, timing in supplements_daily:
            supplement = Supplement(
                user_id=user.id,
                date=supp_date,
                name=supp_name,
                dosage=dosage,
                time_of_day=timing
            )
            db.session.add(supplement)

    # Create workout templates for "My Schedule" (matches the workout history pattern)
    workout_templates_data = [
        {
            'name': 'Push Day',
            'day_of_week': 0,  # Monday
            'description': 'Chest, Shoulders, and Triceps',
            'exercises': [
                ('Bench Press', 4, 8, 185, 180),
                ('Incline Dumbbell Press', 4, 10, 70, 90),
                ('Overhead Press', 3, 8, 115, 120),
                ('Tricep Pushdowns', 3, 12, 50, 90),
                ('Lateral Raises', 3, 15, 20, 60)
            ]
        },
        {
            'name': 'Pull Day',
            'day_of_week': 1,  # Tuesday
            'description': 'Back and Biceps',
            'exercises': [
                ('Deadlift', 4, 5, 275, 240),
                ('Pull-ups', 4, 10, 0, 120),
                ('Barbell Rows', 4, 8, 185, 120),
                ('Face Pulls', 3, 15, 40, 90),
                ('Hammer Curls', 3, 12, 35, 90)
            ]
        },
        {
            'name': 'Leg Day',
            'day_of_week': 3,  # Thursday
            'description': 'Quads, Hamstrings, and Calves',
            'exercises': [
                ('Squats', 4, 8, 225, 180),
                ('Romanian Deadlifts', 4, 10, 185, 120),
                ('Leg Press', 3, 12, 360, 90),
                ('Leg Curls', 3, 12, 90, 90),
                ('Calf Raises', 4, 15, 135, 60)
            ]
        },
        {
            'name': 'Upper Body',
            'day_of_week': 5,  # Saturday
            'description': 'Full Upper Body',
            'exercises': [
                ('Bench Press', 3, 10, 165, 120),
                ('Lat Pulldowns', 3, 10, 140, 90),
                ('Dumbbell Rows', 3, 12, 65, 90),
                ('Dumbbell Flyes', 3, 12, 30, 90),
                ('Cable Curls', 3, 15, 40, 60)
            ]
        }
    ]

    for template_data in workout_templates_data:
        template = WorkoutTemplate(
            user_id=user.id,
            name=template_data['name'],
            description=template_data['description'],
            day_of_week=template_data['day_of_week']
        )
        db.session.add(template)
        db.session.flush()

        for idx, (ex_name, sets, reps, weight, rest) in enumerate(template_data['exercises']):
            template_exercise = TemplateExercise(
                template_id=template.id,
                name=ex_name,
                sets=sets,
                reps=reps,
                weight=weight,
                rest_time=rest,
                order=idx
            )
            db.session.add(template_exercise)

    db.session.commit()
    print(f"[SUCCESS] Demo data populated for user '{user.username}'")

# Initialization moved to run only when app starts, not when imported
# This prevents issues during migration runs
def initialize_app():
    """Initialize app on first startup - create admin user and cleanup old drafts"""
    with app.app_context():
        create_admin_user()
        cleanup_old_drafts()

# Only run initialization when the app is run directly (not during imports/migrations)
if __name__ == '__main__':
    initialize_app()

# Make version available to all templates
@app.context_processor
def inject_version():
    return {'app_version': VERSION}

# ===== AUTHENTICATION ROUTES =====

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember_me)
            # Mark session as permanent if remember_me is checked
            if remember_me:
                session.permanent = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validation
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters')

        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')

        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email already registered')

        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        # Redirect with new_user flag to trigger onboarding tour
        return redirect(url_for('index', new_user='true'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/demo')
def demo():
    """Demo mode: Create/reset demo user and auto-login with populated data"""
    try:
        demo_username = 'demo_user'
        demo_email = 'demo@fitglyph.com'
        demo_password = 'demo123'

        # Check if demo user exists
        demo_user = User.query.filter_by(username=demo_username).first()

        if not demo_user:
            # Create demo user
            demo_user = User(username=demo_username, email=demo_email)
            demo_user.set_password(demo_password)
            db.session.add(demo_user)
            db.session.commit()
            print(f"[SUCCESS] Demo user '{demo_username}' created!")

        # Reset demo data every time (keeps it fresh for recruiters)
        try:
            populate_demo_data(demo_user)
        except Exception as e:
            print(f"[ERROR] Failed to populate demo data: {e}")
            # Continue anyway - user can still be logged in even if demo data fails
            db.session.rollback()

        # Auto-login the demo user
        login_user(demo_user, remember=False)
        session.permanent = False  # Demo session expires when browser closes

        # Redirect to home with a demo flag
        return redirect(url_for('index', demo='true'))

    except Exception as e:
        print(f"[ERROR] Demo mode failed: {e}")
        db.session.rollback()
        flash('Demo mode encountered an error. Please try again or register a new account.', 'error')
        return redirect(url_for('login'))

# ===== MAIN ROUTES =====

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/log', methods=['GET', 'POST'])
@login_required
def log_workout():
    if request.method == 'POST':
        data = request.get_json()

        workout = Workout(
            user_id=current_user.id,
            date=datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
            notes=data.get('notes', ''),
            template_id=data.get('template_id')
        )
        db.session.add(workout)
        db.session.flush()

        for ex in data.get('exercises', []):
            import json
            # Handle weight being optional for bodyweight exercises
            weight_value = ex.get('weight')
            if weight_value is not None and weight_value != '':
                weight_value = float(weight_value)
            else:
                weight_value = None

            exercise = Exercise(
                workout_id=workout.id,
                name=ex['name'],
                sets=int(ex['sets']),
                reps=int(ex['reps']),
                weight=weight_value,
                rest_time=int(ex.get('rest_time', 0)),
                set_data=json.dumps(ex.get('set_data')) if ex.get('set_data') else None,
                is_superset=bool(ex.get('is_superset', False)),
                superset_exercise_name=ex.get('superset_exercise_name')
            )
            db.session.add(exercise)

        db.session.commit()
        return jsonify({'success': True, 'workout_id': workout.id})

    return render_template('log.html')

@app.route('/history')
@login_required
def history():
    # Exclude draft workouts from history
    workouts = Workout.query.filter_by(user_id=current_user.id, is_draft=False).order_by(Workout.date.desc()).all()
    return render_template('history.html', workouts=workouts)

@app.route('/api/workouts')
@login_required
def get_workouts():
    # Exclude draft workouts
    workouts = Workout.query.filter_by(user_id=current_user.id, is_draft=False).order_by(Workout.date.desc()).all()
    return jsonify([w.to_dict() for w in workouts])

@app.route('/api/workouts/<int:workout_id>')
@login_required
def get_workout(workout_id):
    workout = Workout.query.filter_by(id=workout_id, user_id=current_user.id).first_or_404()
    return jsonify(workout.to_dict())

@app.route('/api/workouts/<int:workout_id>', methods=['DELETE'])
@login_required
def delete_workout(workout_id):
    workout = Workout.query.filter_by(id=workout_id, user_id=current_user.id).first_or_404()
    db.session.delete(workout)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/workouts/<int:workout_id>', methods=['PUT'])
@login_required
def update_workout(workout_id):
    workout = Workout.query.filter_by(id=workout_id, user_id=current_user.id).first_or_404()
    data = request.get_json()

    # Update workout date and notes
    if 'date' in data:
        workout.date = datetime.fromisoformat(data['date'])
    if 'notes' in data:
        workout.notes = data['notes']

    # Update exercises if provided
    if 'exercises' in data:
        # Delete existing exercises
        Exercise.query.filter_by(workout_id=workout.id).delete()

        # Add updated exercises
        for ex in data['exercises']:
            import json
            # Handle weight being optional for bodyweight exercises
            weight_value = ex.get('weight')
            if weight_value is not None and weight_value != '':
                weight_value = float(weight_value)
            else:
                weight_value = None

            exercise = Exercise(
                workout_id=workout.id,
                name=ex['name'],
                sets=int(ex['sets']),
                reps=int(ex['reps']),
                weight=weight_value,
                rest_time=int(ex.get('rest_time', 0)),
                set_data=json.dumps(ex.get('set_data')) if ex.get('set_data') else None,
                is_superset=bool(ex.get('is_superset', False)),
                superset_exercise_name=ex.get('superset_exercise_name')
            )
            db.session.add(exercise)

    db.session.commit()
    return jsonify({'success': True, 'workout': workout.to_dict()})

# ===== DRAFT WORKOUT API =====

@app.route('/api/workouts/draft', methods=['GET'])
@login_required
def get_draft_workout():
    """Get the current user's draft workout (if any)"""
    draft = Workout.query.filter_by(user_id=current_user.id, is_draft=True).first()

    if draft:
        return jsonify({'success': True, 'has_draft': True, 'workout': draft.to_dict()})
    else:
        return jsonify({'success': True, 'has_draft': False, 'workout': None})

@app.route('/api/workouts/draft', methods=['POST'])
@login_required
def save_draft_workout():
    """Create or update a draft workout"""
    import json
    data = request.get_json()

    # Check for existing draft
    draft = Workout.query.filter_by(user_id=current_user.id, is_draft=True).first()

    if draft:
        # Update existing draft
        if 'date' in data:
            draft.date = datetime.fromisoformat(data['date'])
        if 'notes' in data:
            draft.notes = data.get('notes', '')
        if 'template_id' in data:
            draft.template_id = data.get('template_id')

        # Delete existing exercises and re-add
        Exercise.query.filter_by(workout_id=draft.id).delete()
    else:
        # Create new draft
        draft = Workout(
            user_id=current_user.id,
            date=datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
            notes=data.get('notes', ''),
            is_draft=True,
            template_id=data.get('template_id')
        )
        db.session.add(draft)
        db.session.flush()  # Get the ID

    # Add exercises
    for ex in data.get('exercises', []):
        # Handle weight being optional for bodyweight exercises
        weight_value = ex.get('weight')
        if weight_value is not None and weight_value != '':
            weight_value = float(weight_value)
        else:
            weight_value = None

        exercise = Exercise(
            workout_id=draft.id,
            name=ex['name'],
            sets=int(ex.get('sets', 1)),
            reps=int(ex.get('reps', 0)),
            weight=weight_value,
            rest_time=int(ex.get('rest_time', 0)),
            set_data=json.dumps(ex.get('set_data')) if ex.get('set_data') else None,
            is_superset=bool(ex.get('is_superset', False)),
            superset_exercise_name=ex.get('superset_exercise_name')
        )
        db.session.add(exercise)

    db.session.commit()
    return jsonify({'success': True, 'workout': draft.to_dict()})

@app.route('/api/workouts/draft/complete', methods=['POST'])
@login_required
def complete_draft_workout():
    """Convert a draft workout to a completed workout"""
    import json
    data = request.get_json()

    draft = Workout.query.filter_by(user_id=current_user.id, is_draft=True).first()

    if not draft:
        return jsonify({'success': False, 'message': 'No draft workout found'}), 404

    # Update with final data if provided
    if 'date' in data:
        draft.date = datetime.fromisoformat(data['date'])
    if 'notes' in data:
        draft.notes = data.get('notes', '')

    # Update exercises if provided
    if 'exercises' in data:
        Exercise.query.filter_by(workout_id=draft.id).delete()

        for ex in data.get('exercises', []):
            weight_value = ex.get('weight')
            if weight_value is not None and weight_value != '':
                weight_value = float(weight_value)
            else:
                weight_value = None

            exercise = Exercise(
                workout_id=draft.id,
                name=ex['name'],
                sets=int(ex.get('sets', 1)),
                reps=int(ex.get('reps', 0)),
                weight=weight_value,
                rest_time=int(ex.get('rest_time', 0)),
                set_data=json.dumps(ex.get('set_data')) if ex.get('set_data') else None,
                is_superset=bool(ex.get('is_superset', False)),
                superset_exercise_name=ex.get('superset_exercise_name')
            )
            db.session.add(exercise)

    # Mark as complete (no longer a draft)
    draft.is_draft = False
    db.session.commit()

    return jsonify({'success': True, 'workout_id': draft.id, 'workout': draft.to_dict()})

@app.route('/api/workouts/draft', methods=['DELETE'])
@login_required
def delete_draft_workout():
    """Discard/delete the current draft workout"""
    draft = Workout.query.filter_by(user_id=current_user.id, is_draft=True).first()

    if draft:
        db.session.delete(draft)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Draft discarded'})
    else:
        return jsonify({'success': True, 'message': 'No draft to discard'})

@app.route('/progress')
@login_required
def progress():
    return render_template('progress.html')

@app.route('/api/progress/<exercise_name>')
@login_required
def get_exercise_progress(exercise_name):
    exercises = Exercise.query.join(Workout).filter(
        Exercise.name == exercise_name,
        Workout.user_id == current_user.id
    ).order_by(Workout.date.asc()).all()

    data = [{
        'date': ex.workout.date.strftime('%Y-%m-%d'),
        'weight': ex.weight,
        'reps': ex.reps,
        'sets': ex.sets
    } for ex in exercises]

    return jsonify(data)

@app.route('/api/exercise_names')
@login_required
def get_exercise_names():
    exercises = db.session.query(Exercise.name).join(Workout).filter(
        Workout.user_id == current_user.id
    ).distinct().all()
    return jsonify([ex[0] for ex in exercises])

@app.route('/body_metrics', methods=['GET', 'POST'])
@login_required
def body_metrics():
    if request.method == 'POST':
        data = request.get_json()
        metric = BodyMetrics(
            user_id=current_user.id,
            date=datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
            weight=float(data['weight']) if data.get('weight') else None,
            height=float(data['height']) if data.get('height') else None
        )
        db.session.add(metric)
        db.session.commit()
        return jsonify({'success': True})

    return render_template('body_metrics.html')

@app.route('/api/body_metrics')
@login_required
def get_body_metrics():
    metrics = BodyMetrics.query.filter_by(user_id=current_user.id).order_by(BodyMetrics.date.desc()).all()
    return jsonify([m.to_dict() for m in metrics])

@app.route('/api/calendar_data')
@login_required
def calendar_data():
    # Exclude draft workouts from calendar
    workouts = Workout.query.filter_by(user_id=current_user.id, is_draft=False).all()
    data = {}
    for w in workouts:
        date_str = w.date.strftime('%Y-%m-%d')
        if date_str not in data:
            data[date_str] = []
        data[date_str].append({
            'id': w.id,
            'exercises': [ex.to_dict() for ex in w.exercises],  # Include full exercise details
            'exercise_count': len(w.exercises),
            'notes': w.notes,
            'date': w.date.isoformat() + 'Z',  # Return as ISO format with UTC marker
            'template_id': w.template_id,
            'template_color': w.template.color if w.template else None,
            'template_name': w.template.name if w.template else None
        })
    return jsonify(data)

# ===== NUTRITION TRACKING =====

# Helper function for relevance scoring
def calculate_relevance_score(query, food_item, source='openfoodfacts'):
    """
    Calculate relevance score for a food item based on query match quality.
    Higher scores = better matches. Range: 0-100
    """
    query = query.lower().strip()
    query_words = query.split()

    # Extract searchable fields based on source
    if source == 'openfoodfacts':
        product_name = food_item.get('product_name', '').lower()
        brand = food_item.get('brands', '').lower()
        search_text = f"{product_name} {brand}"
    else:  # USDA
        search_text = food_item.get('description', '').lower()

    score = 0

    # SCORING RULES (prioritized by impact):

    # 1. Exact phrase match (highest priority) - +50 points
    if query in search_text:
        score += 50
        # Bonus if it's at the start
        if search_text.startswith(query):
            score += 15

    # 2. All query words present - +30 points
    all_words_present = all(word in search_text for word in query_words)
    if all_words_present:
        score += 30

    # 3. Product name vs brand weighting (OpenFoodFacts only)
    if source == 'openfoodfacts':
        product_name_matches = sum(word in product_name for word in query_words)
        brand_matches = sum(word in brand for word in query_words)

        # Product name matches worth more than brand matches
        score += product_name_matches * 8
        score += brand_matches * 3
    else:
        # USDA: count word matches in description
        word_matches = sum(word in search_text for word in query_words)
        score += word_matches * 8

    # 4. Penalize very long names (likely less specific) - up to -10 points
    word_count = len(search_text.split())
    if word_count > 10:
        score -= min(10, (word_count - 10) * 2)

    # 5. Bonus for exact word boundaries (whole word matches) - +5 per word
    for word in query_words:
        if f" {word} " in f" {search_text} " or search_text.startswith(f"{word} ") or search_text.endswith(f" {word}"):
            score += 5

    return max(0, min(100, score))  # Clamp between 0-100


def is_valid_nutrition_data(nutriments, source='openfoodfacts'):
    """Validate that nutrition data is complete and realistic"""
    if source == 'openfoodfacts':
        calories = nutriments.get('energy-kcal_100g', 0)
        protein = nutriments.get('proteins_100g', 0)
        carbs = nutriments.get('carbohydrates_100g', 0)
        fats = nutriments.get('fat_100g', 0)
    else:  # USDA (pass nutrients dict directly)
        calories = nutriments.get('calories', 0)
        protein = nutriments.get('protein', 0)
        carbs = nutriments.get('carbs', 0)
        fats = nutriments.get('fats', 0)

    # Must have calories
    if calories <= 0:
        return False

    # Must have at least one macro (some items might have only one)
    if protein == 0 and carbs == 0 and fats == 0:
        return False

    # Sanity check: macros shouldn't exceed calorie-realistic values
    # Rough check: protein + carbs = ~4 cal/g, fat = ~9 cal/g
    calculated_calories = (protein * 4) + (carbs * 4) + (fats * 9)

    # Allow 50% deviation (some rounding/fiber issues)
    if calculated_calories > 0:
        deviation = abs(calories - calculated_calories) / calculated_calories
        if deviation > 0.5:
            return False

    return True


# USDA API nutrition lookup
def search_openfoodfacts(food_name):
    """Search OpenFoodFacts API for food by name with relevance scoring"""
    url = f'https://world.openfoodfacts.org/cgi/search.pl'
    params = {
        'search_terms': food_name,
        'page_size': 20,  # Fetch more to filter client-side
        'json': 1,
        'fields': 'product_name,brands,nutriments,nutriscore_grade,completeness',
        'search_simple': 1,  # Use simple search
        'sort_by': 'unique_scans_n',  # Sort by popularity
        'tagtype_0': 'states',
        'tag_contains_0': 'contains',
        'tag_0': 'en:nutrition-facts-completed'
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data.get('count', 0) > 0 and 'products' in data:
            scored_results = []

            # Sort by completeness first to prioritize quality data
            products = sorted(
                data['products'][:15],
                key=lambda p: p.get('completeness', 0),
                reverse=True
            )

            for product in products:
                nutriments = product.get('nutriments', {})

                # Use enhanced nutrition validation
                if not nutriments or not is_valid_nutrition_data(nutriments, 'openfoodfacts'):
                    continue

                product_name = product.get('product_name', '')
                brand = product.get('brands', '')

                # Calculate relevance score
                score = calculate_relevance_score(food_name, product, 'openfoodfacts')

                # For multi-word queries, require minimum relevance
                query_words = food_name.lower().split()
                if len(query_words) > 1 and score < 30:
                    continue

                display_name = f"{product_name} ({brand})" if brand else product_name

                scored_results.append({
                    'name': display_name or 'Unknown Product',
                    'serving_size': '100g',
                    'calories': round(nutriments.get('energy-kcal_100g', 0), 1),
                    'protein': round(nutriments.get('proteins_100g', 0), 1),
                    'carbs': round(nutriments.get('carbohydrates_100g', 0), 1),
                    'fats': round(nutriments.get('fat_100g', 0), 1),
                    'fiber': round(nutriments.get('fiber_100g', 0), 1),
                    'source': 'OpenFoodFacts',
                    'relevance_score': score
                })

            # Sort by relevance score (descending)
            scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)

            # Return top 5 without the score
            return [
                {k: v for k, v in r.items() if k != 'relevance_score'}
                for r in scored_results[:5]
            ] if scored_results else None

        return None
    except Exception as e:
        print(f"OpenFoodFacts error: {e}")
        return None

def search_usda(food_name):
    """Search USDA FoodData Central API for food by name with relevance scoring"""
    api_key = os.getenv('USDA_API_KEY', 'DEMO_KEY')

    # Use params dict for better control
    url = 'https://api.nal.usda.gov/fdc/v1/foods/search'
    params = {
        'query': food_name,
        'pageSize': 15,  # Fetch more to filter
        'api_key': api_key,
        'dataType': ['SR Legacy', 'Foundation', 'Survey (FNDDS)'],
        'sortBy': 'dataType.keyword'
    }

    # For multi-word queries, try to require all words
    if len(food_name.split()) > 1:
        params['requireAllWords'] = 'true'

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if 'foods' in data and len(data['foods']) > 0:
            scored_results = []

            for food in data['foods'][:15]:
                # Extract nutrients
                nutrients = {}
                for nutrient in food.get('foodNutrients', []):
                    nutrient_name = nutrient.get('nutrientName', '').lower()
                    nutrient_value = nutrient.get('value', 0)
                    unit_name = nutrient.get('unitName', '').lower()

                    # More flexible calorie detection
                    if ('energy' in nutrient_name or 'calorie' in nutrient_name) and nutrient_value > 0:
                        if 'kcal' in unit_name or 'calories' in unit_name or nutrient_value < 1000:
                            nutrients['calories'] = round(nutrient_value, 1)
                    elif 'protein' in nutrient_name:
                        nutrients['protein'] = round(nutrient_value, 1)
                    elif 'carbohydrate' in nutrient_name and 'fiber' not in nutrient_name:
                        nutrients['carbs'] = round(nutrient_value, 1)
                    elif 'total lipid' in nutrient_name or nutrient_name == 'fat':
                        nutrients['fats'] = round(nutrient_value, 1)
                    elif 'fiber' in nutrient_name:
                        nutrients['fiber'] = round(nutrient_value, 1)

                # Use enhanced nutrition validation
                if not is_valid_nutrition_data(nutrients, 'usda'):
                    continue

                # Calculate relevance score
                score = calculate_relevance_score(food_name, food, 'usda')

                # For multi-word queries, require minimum relevance
                query_words = food_name.lower().split()
                if len(query_words) > 1 and score < 30:
                    continue

                scored_results.append({
                    'name': food.get('description', 'Unknown'),
                    'serving_size': '100g',
                    'calories': nutrients.get('calories', 0),
                    'protein': nutrients.get('protein', 0),
                    'carbs': nutrients.get('carbs', 0),
                    'fats': nutrients.get('fats', 0),
                    'fiber': nutrients.get('fiber', 0),
                    'source': 'USDA',
                    'relevance_score': score
                })

            # Sort by relevance score (descending)
            scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)

            # Return top 5 without the score
            return [
                {k: v for k, v in r.items() if k != 'relevance_score'}
                for r in scored_results[:5]
            ] if scored_results else None

        return None
    except Exception as e:
        print(f"USDA error: {e}")
        return None

@app.route('/api/food/search/<food_name>')
@login_required
def search_food(food_name):
    """Multi-API food search: tries OpenFoodFacts first, falls back to USDA"""
    try:
        # Try OpenFoodFacts first (free, extensive database)
        results = search_openfoodfacts(food_name)

        if results and len(results) > 0:
            return jsonify({
                'success': True,
                'results': results,
                'source': 'OpenFoodFacts'
            })

        # Fallback to USDA if OpenFoodFacts returns nothing
        results = search_usda(food_name)

        if results and len(results) > 0:
            return jsonify({
                'success': True,
                'results': results,
                'source': 'USDA'
            })

        return jsonify({
            'success': False,
            'message': 'No foods found in either database'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Barcode lookup using OpenFoodFacts API
@app.route('/api/food/barcode/<barcode>')
@login_required
def search_barcode(barcode):
    """Look up product nutrition data using barcode via OpenFoodFacts API"""
    url = f'https://world.openfoodfacts.org/api/v2/product/{barcode}.json'

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get('status') == 1 and 'product' in data:
            product = data['product']

            # Extract product name
            product_name = product.get('product_name', 'Unknown Product')

            # Get nutriments (nutrition data per 100g)
            nutriments = product.get('nutriments', {})

            # Extract nutrition info (OpenFoodFacts stores per 100g by default)
            result = {
                'name': product_name,
                'brand': product.get('brands', ''),
                'serving_size': '100g',
                'calories': round(nutriments.get('energy-kcal_100g', 0), 1),
                'protein': round(nutriments.get('proteins_100g', 0), 1),
                'carbs': round(nutriments.get('carbohydrates_100g', 0), 1),
                'fats': round(nutriments.get('fat_100g', 0), 1),
                'fiber': round(nutriments.get('fiber_100g', 0), 1),
                'barcode': barcode
            }

            return jsonify({'success': True, 'product': result})
        else:
            return jsonify({'success': False, 'message': 'Product not found in database'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error looking up barcode: {str(e)}'})

# Log nutrition
@app.route('/nutrition', methods=['GET', 'POST'])
@login_required
def log_nutrition():
    if request.method == 'POST':
        data = request.get_json()

        meal = Meal(
            user_id=current_user.id,
            date=datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
            meal_type=data.get('meal_type', 'Snack'),
            notes=data.get('notes', '')
        )
        db.session.add(meal)
        db.session.flush()

        for item in data.get('food_items', []):
            # Convert quantity based on unit to calculate actual nutrition
            quantity = float(item.get('quantity', 1.0))
            unit = item.get('unit', 'g')

            # Convert to base unit (100g)
            base_quantity = convert_to_base_unit(quantity, unit) / 100.0

            food_item = FoodItem(
                meal_id=meal.id,
                name=item['name'],
                serving_size=item.get('serving_size', '100g'),
                quantity=quantity,
                unit=unit,
                # Store per-serving nutrition (already scaled by quantity)
                calories=float(item.get('calories', 0)) * base_quantity,
                protein=float(item.get('protein', 0)) * base_quantity,
                carbs=float(item.get('carbs', 0)) * base_quantity,
                fats=float(item.get('fats', 0)) * base_quantity,
                fiber=float(item.get('fiber', 0)) * base_quantity
            )
            db.session.add(food_item)

        db.session.commit()
        return jsonify({'success': True, 'meal_id': meal.id})

    return render_template('nutrition.html')

# Get all nutrition data
@app.route('/api/nutrition')
@login_required
def get_nutrition():
    meals = Meal.query.filter_by(user_id=current_user.id).order_by(Meal.date.desc()).limit(50).all()
    return jsonify([m.to_dict() for m in meals])

# Get daily nutrition summary
@app.route('/api/nutrition/daily/<date>')
@login_required
def get_daily_nutrition(date):
    target_date = datetime.fromisoformat(date)
    meals = Meal.query.filter(
        Meal.user_id == current_user.id,
        func.date(Meal.date) == target_date.date()
    ).all()

    daily_totals = {
        'date': date,
        'calories': 0,
        'protein': 0,
        'carbs': 0,
        'fats': 0,
        'meals': []
    }

    for meal in meals:
        meal_data = meal.to_dict()
        daily_totals['meals'].append(meal_data)
        daily_totals['calories'] += meal_data['totals']['calories']
        daily_totals['protein'] += meal_data['totals']['protein']
        daily_totals['carbs'] += meal_data['totals']['carbs']
        daily_totals['fats'] += meal_data['totals']['fats']

    return jsonify(daily_totals)

# Delete meal
@app.route('/api/nutrition/<int:meal_id>', methods=['DELETE'])
@login_required
def delete_meal(meal_id):
    meal = Meal.query.filter_by(id=meal_id, user_id=current_user.id).first_or_404()
    db.session.delete(meal)
    db.session.commit()
    return jsonify({'success': True})

# ===== NUTRITION GOALS =====

# Get active nutrition goals
@app.route('/api/nutrition/goals', methods=['GET'])
@login_required
def get_nutrition_goals():
    goals = NutritionGoals.query.filter_by(user_id=current_user.id, is_active=True).first()
    if not goals:
        # Create default goals if none exist
        goals = NutritionGoals(user_id=current_user.id)
        db.session.add(goals)
        db.session.commit()
    return jsonify(goals.to_dict())

# Set nutrition goals
@app.route('/api/nutrition/goals', methods=['POST'])
@login_required
def set_nutrition_goals():
    data = request.get_json()

    # Deactivate old goals for this user
    NutritionGoals.query.filter_by(user_id=current_user.id).update({NutritionGoals.is_active: False})

    # Create new goals
    goals = NutritionGoals(
        user_id=current_user.id,
        calories_goal=int(data.get('calories_goal', 2000)),
        protein_goal=int(data.get('protein_goal', 150)),
        carbs_goal=int(data.get('carbs_goal', 200)),
        fats_goal=int(data.get('fats_goal', 65)),
        is_active=True
    )
    db.session.add(goals)
    db.session.commit()

    return jsonify({'success': True, 'goals': goals.to_dict()})

# Get weekly nutrition summary
@app.route('/api/nutrition/weekly')
@login_required
def get_weekly_nutrition():
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)

    meals = Meal.query.filter(
        Meal.user_id == current_user.id,
        func.date(Meal.date) >= week_ago,
        func.date(Meal.date) <= today
    ).all()

    # Group by date
    daily_data = {}
    for day_offset in range(7):
        date = week_ago + timedelta(days=day_offset)
        date_str = date.strftime('%Y-%m-%d')
        daily_data[date_str] = {
            'date': date_str,
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fats': 0
        }

    for meal in meals:
        date_str = meal.date.strftime('%Y-%m-%d')
        if date_str in daily_data:
            totals = meal.get_totals()
            daily_data[date_str]['calories'] += totals['calories']
            daily_data[date_str]['protein'] += totals['protein']
            daily_data[date_str]['carbs'] += totals['carbs']
            daily_data[date_str]['fats'] += totals['fats']

    # Convert to list sorted by date
    weekly_list = [daily_data[date] for date in sorted(daily_data.keys())]

    return jsonify(weekly_list)

# Get daily nutrition with goals and percentages
@app.route('/api/nutrition/daily/<date>/with-goals')
@login_required
def get_daily_nutrition_with_goals(date):
    target_date = datetime.fromisoformat(date)
    meals = Meal.query.filter(
        Meal.user_id == current_user.id,
        func.date(Meal.date) == target_date.date()
    ).all()

    daily_totals = {
        'date': date,
        'calories': 0,
        'protein': 0,
        'carbs': 0,
        'fats': 0,
        'meals': []
    }

    for meal in meals:
        meal_data = meal.to_dict()
        daily_totals['meals'].append(meal_data)
        daily_totals['calories'] += meal_data['totals']['calories']
        daily_totals['protein'] += meal_data['totals']['protein']
        daily_totals['carbs'] += meal_data['totals']['carbs']
        daily_totals['fats'] += meal_data['totals']['fats']

    # Get goals
    goals = NutritionGoals.query.filter_by(user_id=current_user.id, is_active=True).first()
    if not goals:
        goals = NutritionGoals(user_id=current_user.id)
        db.session.add(goals)
        db.session.commit()

    # Calculate percentages and macro split
    daily_totals['goals'] = goals.to_dict()
    daily_totals['percentages'] = {
        'calories': round((daily_totals['calories'] / goals.calories_goal) * 100, 1) if goals.calories_goal > 0 else 0,
        'protein': round((daily_totals['protein'] / goals.protein_goal) * 100, 1) if goals.protein_goal > 0 else 0,
        'carbs': round((daily_totals['carbs'] / goals.carbs_goal) * 100, 1) if goals.carbs_goal > 0 else 0,
        'fats': round((daily_totals['fats'] / goals.fats_goal) * 100, 1) if goals.fats_goal > 0 else 0
    }

    # Calculate macro split (protein: 4 cal/g, carbs: 4 cal/g, fats: 9 cal/g)
    protein_cals = daily_totals['protein'] * 4
    carbs_cals = daily_totals['carbs'] * 4
    fats_cals = daily_totals['fats'] * 9
    total_cals = protein_cals + carbs_cals + fats_cals

    if total_cals > 0:
        daily_totals['macro_split'] = {
            'protein': round((protein_cals / total_cals) * 100, 1),
            'carbs': round((carbs_cals / total_cals) * 100, 1),
            'fats': round((fats_cals / total_cals) * 100, 1)
        }
    else:
        daily_totals['macro_split'] = {'protein': 0, 'carbs': 0, 'fats': 0}

    return jsonify(daily_totals)

# ===== SUPPLEMENTS =====

# Get supplements for a specific date
@app.route('/api/supplements/daily/<date>')
@login_required
def get_daily_supplements(date):
    target_date = datetime.fromisoformat(date)
    supplements = Supplement.query.filter(
        Supplement.user_id == current_user.id,
        func.date(Supplement.date) == target_date.date()
    ).all()
    return jsonify([s.to_dict() for s in supplements])

# Log a supplement
@app.route('/api/supplements', methods=['POST'])
@login_required
def log_supplement():
    data = request.get_json()

    supplement = Supplement(
        user_id=current_user.id,
        date=datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
        name=data['name'],
        dosage=data.get('dosage', ''),
        time_of_day=data.get('time_of_day', ''),
        notes=data.get('notes', '')
    )
    db.session.add(supplement)
    db.session.commit()

    return jsonify({'success': True, 'supplement_id': supplement.id, 'supplement': supplement.to_dict()})

# Delete a supplement
@app.route('/api/supplements/<int:supplement_id>', methods=['DELETE'])
@login_required
def delete_supplement(supplement_id):
    supplement = Supplement.query.filter_by(id=supplement_id, user_id=current_user.id).first_or_404()
    db.session.delete(supplement)
    db.session.commit()
    return jsonify({'success': True})

# ===== WORKOUT TEMPLATES / MY SCHEDULE =====

# Get all workout templates
@app.route('/api/templates')
@login_required
def get_templates():
    templates = WorkoutTemplate.query.filter_by(user_id=current_user.id).order_by(WorkoutTemplate.created_at.desc()).all()
    return jsonify([t.to_dict() for t in templates])

# Get a specific template
@app.route('/api/templates/<int:template_id>')
@login_required
def get_template(template_id):
    template = WorkoutTemplate.query.filter_by(id=template_id, user_id=current_user.id).first_or_404()
    return jsonify(template.to_dict())

# Create a new template
@app.route('/api/templates', methods=['POST'])
@login_required
def create_template():
    data = request.get_json()

    # Support both old single day and new multiple days
    scheduled_days = data.get('scheduled_days', [])
    single_day = data.get('day_of_week')

    # For backwards compatibility: if old single day is provided, convert to array
    if not scheduled_days and single_day is not None and single_day != '':
        scheduled_days = [int(single_day)]

    template = WorkoutTemplate(
        user_id=current_user.id,
        name=data['name'],
        description=data.get('description', ''),
        color=data.get('color', '#198754'),
        day_of_week=scheduled_days[0] if len(scheduled_days) == 1 else None  # Keep old field for backwards compat
    )
    db.session.add(template)
    db.session.flush()

    # Add scheduled days to association table
    for day in scheduled_days:
        schedule = TemplateSchedule(
            template_id=template.id,
            day_of_week=int(day)
        )
        db.session.add(schedule)

    # Add exercises to template
    for idx, ex in enumerate(data.get('exercises', [])):
        template_exercise = TemplateExercise(
            template_id=template.id,
            name=ex['name'],
            sets=int(ex['sets']),
            reps=int(ex['reps']),
            weight=float(ex.get('weight', 0)),
            rest_time=int(ex.get('rest_time', 0)),
            order=idx,
            is_superset=bool(ex.get('is_superset', False)),
            superset_exercise_name=ex.get('superset_exercise_name')
        )
        db.session.add(template_exercise)

    db.session.commit()
    return jsonify({'success': True, 'template_id': template.id, 'template': template.to_dict()})

# Update a template
@app.route('/api/templates/<int:template_id>', methods=['PUT'])
@login_required
def update_template(template_id):
    template = WorkoutTemplate.query.filter_by(id=template_id, user_id=current_user.id).first_or_404()
    data = request.get_json()

    template.name = data.get('name', template.name)
    template.description = data.get('description', template.description)
    if 'color' in data:
        template.color = data.get('color')

    # Support both old single day and new multiple days
    scheduled_days = data.get('scheduled_days', [])
    single_day = data.get('day_of_week')

    # For backwards compatibility: if old single day is provided, convert to array
    if not scheduled_days and single_day is not None and single_day != '':
        scheduled_days = [int(single_day)]

    # Update old field for backwards compatibility
    template.day_of_week = scheduled_days[0] if len(scheduled_days) == 1 else None

    # Delete existing scheduled days
    TemplateSchedule.query.filter_by(template_id=template.id).delete()

    # Add updated scheduled days
    for day in scheduled_days:
        schedule = TemplateSchedule(
            template_id=template.id,
            day_of_week=int(day)
        )
        db.session.add(schedule)

    # Delete existing exercises
    TemplateExercise.query.filter_by(template_id=template.id).delete()

    # Add updated exercises
    for idx, ex in enumerate(data.get('exercises', [])):
        template_exercise = TemplateExercise(
            template_id=template.id,
            name=ex['name'],
            sets=int(ex['sets']),
            reps=int(ex['reps']),
            weight=float(ex.get('weight', 0)),
            rest_time=int(ex.get('rest_time', 0)),
            order=idx,
            is_superset=bool(ex.get('is_superset', False)),
            superset_exercise_name=ex.get('superset_exercise_name')
        )
        db.session.add(template_exercise)

    db.session.commit()
    return jsonify({'success': True, 'template': template.to_dict()})

# Delete a template
@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
@login_required
def delete_template(template_id):
    template = WorkoutTemplate.query.filter_by(id=template_id, user_id=current_user.id).first_or_404()
    db.session.delete(template)
    db.session.commit()
    return jsonify({'success': True})

# Get today's scheduled workout
@app.route('/api/schedule/today')
@login_required
def get_todays_workout():
    from datetime import datetime
    # Get current day of week (0=Monday, 6=Sunday)
    today = datetime.now().weekday()

    # Find template scheduled for today - check both new and old methods
    # First try the new TemplateSchedule table
    scheduled_template = db.session.query(WorkoutTemplate).join(
        TemplateSchedule,
        WorkoutTemplate.id == TemplateSchedule.template_id
    ).filter(
        WorkoutTemplate.user_id == current_user.id,
        TemplateSchedule.day_of_week == today
    ).first()

    # Fall back to old single day_of_week field for backwards compatibility
    if not scheduled_template:
        scheduled_template = WorkoutTemplate.query.filter_by(
            user_id=current_user.id,
            day_of_week=today
        ).first()

    if scheduled_template:
        return jsonify({
            'success': True,
            'scheduled': True,
            'template': scheduled_template.to_dict()
        })
    else:
        return jsonify({
            'success': True,
            'scheduled': False,
            'message': 'Rest Day'
        })

# My Schedule page route
@app.route('/schedule')
@login_required
def schedule():
    return render_template('schedule.html')

# Settings page route
@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

# User timezone settings API
@app.route('/api/user/timezone', methods=['GET'])
@login_required
def get_timezone():
    """Get the current user's timezone offset"""
    return jsonify({
        'timezone_offset': current_user.timezone_offset
    })

@app.route('/api/user/timezone', methods=['POST'])
@login_required
def update_timezone():
    """Update the current user's timezone offset"""
    data = request.get_json()
    timezone_offset = data.get('timezone_offset', 0)

    # Validate timezone offset is within valid range
    if timezone_offset < -12 or timezone_offset > 12:
        return jsonify({'success': False, 'error': 'Invalid timezone offset'}), 400

    # Update user's timezone offset
    current_user.timezone_offset = timezone_offset
    db.session.commit()

    return jsonify({'success': True, 'timezone_offset': timezone_offset})

# Consistency tracking endpoint
@app.route('/api/consistency')
@login_required
def get_consistency():
    """
    Calculate workout consistency based on scheduled workouts vs actual workouts
    Query params: days (default 30) - number of days to look back
    """
    from datetime import datetime, timedelta

    # Get number of days to look back (default 30)
    days = int(request.args.get('days', 30))

    # Build a set of scheduled day_of_week values from both old and new methods
    scheduled_days_of_week = set()

    # Get scheduled days from new TemplateSchedule table
    template_schedules = db.session.query(TemplateSchedule).join(
        WorkoutTemplate,
        TemplateSchedule.template_id == WorkoutTemplate.id
    ).filter(
        WorkoutTemplate.user_id == current_user.id
    ).all()

    for schedule in template_schedules:
        scheduled_days_of_week.add(schedule.day_of_week)

    # Also check old day_of_week field for backwards compatibility
    old_scheduled_templates = WorkoutTemplate.query.filter_by(
        user_id=current_user.id
    ).filter(WorkoutTemplate.day_of_week.isnot(None)).all()

    for template in old_scheduled_templates:
        scheduled_days_of_week.add(template.day_of_week)

    # If no scheduled workouts, return 0%
    if not scheduled_days_of_week:
        return jsonify({
            'adherence_percentage': 0,
            'scheduled_days': 0,
            'completed_days': 0,
            'total_workouts': 0,
            'message': 'No workouts scheduled'
        })

    # Get all workouts in the date range (exclude drafts)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    workouts = Workout.query.filter(
        Workout.user_id == current_user.id,
        Workout.is_draft == False,
        Workout.date >= start_date,
        Workout.date <= end_date
    ).all()

    # Group workouts by date (date only, not time)
    workout_dates = set()
    for w in workouts:
        workout_dates.add(w.date.date())

    # Count scheduled days and completed days
    scheduled_count = 0
    completed_count = 0

    # Iterate through each day in the range
    current_date = start_date.date()
    end = end_date.date()

    while current_date <= end:
        # Check if this day of week is scheduled
        day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday

        if day_of_week in scheduled_days_of_week:
            scheduled_count += 1

            # Check if there was a workout on this date
            if current_date in workout_dates:
                completed_count += 1

        current_date += timedelta(days=1)

    # Calculate adherence percentage
    adherence_percentage = (completed_count / scheduled_count * 100) if scheduled_count > 0 else 0

    return jsonify({
        'adherence_percentage': round(adherence_percentage, 1),
        'scheduled_days': scheduled_count,
        'completed_days': completed_count,
        'total_workouts': len(workouts),
        'period_days': days
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
