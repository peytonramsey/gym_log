from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Workout, Exercise, BodyMetrics, Meal, FoodItem, NutritionGoals, WorkoutTemplate, TemplateExercise
from datetime import datetime, timedelta
from sqlalchemy import func
import requests
import os
from dotenv import load_dotenv

load_dotenv()

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

db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# ===== AUTHENTICATION ROUTES =====

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
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
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
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
            notes=data.get('notes', '')
        )
        db.session.add(workout)
        db.session.flush()

        for ex in data.get('exercises', []):
            exercise = Exercise(
                workout_id=workout.id,
                name=ex['name'],
                sets=int(ex['sets']),
                reps=int(ex['reps']),
                weight=float(ex['weight']),
                rest_time=int(ex.get('rest_time', 0))
            )
            db.session.add(exercise)

        db.session.commit()
        return jsonify({'success': True, 'workout_id': workout.id})

    return render_template('log.html')

@app.route('/history')
@login_required
def history():
    workouts = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date.desc()).all()
    return render_template('history.html', workouts=workouts)

@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

@app.route('/api/workouts')
@login_required
def get_workouts():
    workouts = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date.desc()).all()
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
    workouts = Workout.query.filter_by(user_id=current_user.id).all()
    data = {}
    for w in workouts:
        date_str = w.date.strftime('%Y-%m-%d')
        if date_str not in data:
            data[date_str] = []
        data[date_str].append({
            'id': w.id,
            'exercises': len(w.exercises),
            'notes': w.notes
        })
    return jsonify(data)

# ===== NUTRITION TRACKING =====

# USDA API nutrition lookup
@app.route('/api/food/search/<food_name>')
@login_required
def search_food(food_name):
    """Search for food nutrition data using USDA API"""
    # USDA FoodData Central API (no key needed for basic search)
    url = f'https://api.nal.usda.gov/fdc/v1/foods/search?query={food_name}&pageSize=5&api_key=DEMO_KEY'

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if 'foods' in data and len(data['foods']) > 0:
            results = []
            for food in data['foods'][:5]:
                # Extract nutrients
                nutrients = {}
                for nutrient in food.get('foodNutrients', []):
                    nutrient_name = nutrient.get('nutrientName', '')
                    nutrient_value = nutrient.get('value', 0)

                    if 'Energy' in nutrient_name and 'kcal' in nutrient.get('unitName', ''):
                        nutrients['calories'] = round(nutrient_value, 1)
                    elif nutrient_name == 'Protein':
                        nutrients['protein'] = round(nutrient_value, 1)
                    elif 'Carbohydrate' in nutrient_name:
                        nutrients['carbs'] = round(nutrient_value, 1)
                    elif 'Total lipid' in nutrient_name or nutrient_name == 'Fat':
                        nutrients['fats'] = round(nutrient_value, 1)
                    elif 'Fiber' in nutrient_name:
                        nutrients['fiber'] = round(nutrient_value, 1)

                results.append({
                    'name': food.get('description', 'Unknown'),
                    'serving_size': '100g',
                    'calories': nutrients.get('calories', 0),
                    'protein': nutrients.get('protein', 0),
                    'carbs': nutrients.get('carbs', 0),
                    'fats': nutrients.get('fats', 0),
                    'fiber': nutrients.get('fiber', 0)
                })

            return jsonify({'success': True, 'results': results})
        else:
            return jsonify({'success': False, 'message': 'No foods found'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

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

    template = WorkoutTemplate(
        user_id=current_user.id,
        name=data['name'],
        description=data.get('description', '')
    )
    db.session.add(template)
    db.session.flush()

    # Add exercises to template
    for idx, ex in enumerate(data.get('exercises', [])):
        template_exercise = TemplateExercise(
            template_id=template.id,
            name=ex['name'],
            sets=int(ex['sets']),
            reps=int(ex['reps']),
            weight=float(ex.get('weight', 0)),
            rest_time=int(ex.get('rest_time', 0)),
            order=idx
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
            order=idx
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

# My Schedule page route
@app.route('/schedule')
@login_required
def schedule():
    return render_template('schedule.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
