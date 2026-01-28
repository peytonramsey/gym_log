from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Avoid PostgreSQL reserved word 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    timezone_offset = db.Column(db.Integer, default=0)  # Hours offset from UTC (e.g., -5 for EST)

    # Relationships
    workouts = db.relationship('Workout', backref='user', lazy=True, cascade='all, delete-orphan')
    meals = db.relationship('Meal', backref='user', lazy=True, cascade='all, delete-orphan')
    body_metrics = db.relationship('BodyMetrics', backref='user', lazy=True, cascade='all, delete-orphan')
    templates = db.relationship('WorkoutTemplate', backref='user', lazy=True, cascade='all, delete-orphan')
    nutrition_goals = db.relationship('NutritionGoals', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.strftime('%Y-%m-%d')
        }

class BodyMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    weight = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'weight': self.weight,
            'height': self.height
        }

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.String(500))
    is_draft = db.Column(db.Boolean, default=False, nullable=False)  # Draft workouts are auto-saved in progress
    template_id = db.Column(db.Integer, db.ForeignKey('workout_template.id'), nullable=True)  # Track which template was used
    exercises = db.relationship('Exercise', backref='workout', lazy=True, cascade='all, delete-orphan')
    template = db.relationship('WorkoutTemplate', backref='workouts')

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() + 'Z',  # Return as ISO format with UTC marker
            'notes': self.notes,
            'is_draft': self.is_draft,
            'template_id': self.template_id,
            'template_color': self.template.color if self.template else None,
            'template_name': self.template.name if self.template else None,
            'exercises': [ex.to_dict() for ex in self.exercises]
        }

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=True)  # Nullable for bodyweight exercises
    rest_time = db.Column(db.Integer, nullable=True)  # rest time in seconds
    set_data = db.Column(db.Text, nullable=True)  # JSON array of individual sets: [{"set_number": 1, "reps": 10, "weight": 135}, ...]

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'name': self.name,
            'sets': self.sets,
            'reps': self.reps,
            'weight': self.weight,
            'rest_time': self.rest_time,
            'set_data': json.loads(self.set_data) if self.set_data else None
        }

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    meal_type = db.Column(db.String(20))  # Breakfast, Lunch, Dinner, Snack
    notes = db.Column(db.String(200))

    # Relationship with food items
    food_items = db.relationship('FoodItem', backref='meal', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() + 'Z',  # Return as ISO format with UTC marker
            'meal_type': self.meal_type,
            'notes': self.notes,
            'food_items': [item.to_dict() for item in self.food_items],
            'totals': self.get_totals()
        }

    def get_totals(self):
        totals = {
            'calories': sum(item.calories for item in self.food_items),
            'protein': sum(item.protein for item in self.food_items),
            'carbs': sum(item.carbs for item in self.food_items),
            'fats': sum(item.fats for item in self.food_items)
        }
        return totals

class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    serving_size = db.Column(db.String(50))
    quantity = db.Column(db.Float, default=1.0)
    unit = db.Column(db.String(20), default='g')  # g, oz, ml, fl oz, cup, tbsp, tsp, serving

    # Nutrition info (per 100g or 100ml base)
    calories = db.Column(db.Float, default=0)
    protein = db.Column(db.Float, default=0)  # grams
    carbs = db.Column(db.Float, default=0)    # grams
    fats = db.Column(db.Float, default=0)     # grams
    fiber = db.Column(db.Float, default=0)    # grams (optional)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'serving_size': self.serving_size,
            'quantity': self.quantity,
            'unit': self.unit,
            'calories': self.calories,
            'protein': self.protein,
            'carbs': self.carbs,
            'fats': self.fats,
            'fiber': self.fiber
        }

class NutritionGoals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Daily goals
    calories_goal = db.Column(db.Integer, default=2000)
    protein_goal = db.Column(db.Integer, default=150)  # grams
    carbs_goal = db.Column(db.Integer, default=200)    # grams
    fats_goal = db.Column(db.Integer, default=65)      # grams

    # Whether this is the active goal
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'calories_goal': self.calories_goal,
            'protein_goal': self.protein_goal,
            'carbs_goal': self.carbs_goal,
            'fats_goal': self.fats_goal,
            'is_active': self.is_active
        }

class Supplement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50))  # e.g., "1000mg", "2 capsules"
    time_of_day = db.Column(db.String(20))  # Morning, Afternoon, Evening, Night
    notes = db.Column(db.String(200))

    user = db.relationship('User', backref='supplements')

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d %H:%M'),
            'name': self.name,
            'dosage': self.dosage,
            'time_of_day': self.time_of_day,
            'notes': self.notes
        }

class TemplateSchedule(db.Model):
    """Association table for templates and their scheduled days"""
    __tablename__ = 'template_schedule'

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('workout_template.id', ondelete='CASCADE'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 1=Tuesday, ..., 6=Sunday

    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'day_of_week': self.day_of_week
        }

class WorkoutTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Push Day 1", "Pull Day"
    description = db.Column(db.String(500))
    day_of_week = db.Column(db.Integer, nullable=True)  # DEPRECATED: Use scheduled_days instead
    color = db.Column(db.String(7), default='#198754')  # Hex color code for calendar display
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    template_exercises = db.relationship('TemplateExercise', backref='template', lazy=True, cascade='all, delete-orphan')
    scheduled_days = db.relationship('TemplateSchedule', backref='template', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        # Get scheduled days from new table, or fall back to old single day field for backwards compatibility
        days_list = [s.day_of_week for s in self.scheduled_days] if self.scheduled_days else (
            [self.day_of_week] if self.day_of_week is not None else []
        )

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'day_of_week': self.day_of_week,  # Keep for backwards compatibility
            'scheduled_days': sorted(days_list),  # New field: array of days
            'color': self.color or '#198754',  # Default green if not set
            'created_at': self.created_at.strftime('%Y-%m-%d'),
            'exercises': [ex.to_dict() for ex in self.template_exercises]
        }

class TemplateExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('workout_template.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, default=0)  # Default weight (optional)
    rest_time = db.Column(db.Integer, nullable=True)  # rest time in seconds
    order = db.Column(db.Integer, default=0)  # order of exercise in the workout

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sets': self.sets,
            'reps': self.reps,
            'weight': self.weight,
            'rest_time': self.rest_time,
            'order': self.order
        }

class WeightPrediction(db.Model):
    """Track ML predictions vs actual outcomes for model improvement"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise_name = db.Column(db.String(100), nullable=False)
    predicted_weight = db.Column(db.Float, nullable=False)
    confidence_lower = db.Column(db.Float, nullable=True)  # Lower bound of confidence interval
    confidence_upper = db.Column(db.Float, nullable=True)  # Upper bound of confidence interval
    actual_weight = db.Column(db.Float, nullable=True)  # Filled in after workout
    actual_completed = db.Column(db.Boolean, nullable=True)  # Did user complete all sets?
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    workout_date = db.Column(db.DateTime, nullable=True)  # When actual workout happened
    model_version = db.Column(db.String(50), default='v1.0')  # Track model version
    features_used = db.Column(db.Text, nullable=True)  # JSON of features used for prediction

    user = db.relationship('User', backref='weight_predictions')

    def to_dict(self):
        return {
            'id': self.id,
            'exercise_name': self.exercise_name,
            'predicted_weight': self.predicted_weight,
            'confidence_lower': self.confidence_lower,
            'confidence_upper': self.confidence_upper,
            'actual_weight': self.actual_weight,
            'actual_completed': self.actual_completed,
            'prediction_date': self.prediction_date.strftime('%Y-%m-%d %H:%M'),
            'workout_date': self.workout_date.strftime('%Y-%m-%d %H:%M') if self.workout_date else None,
            'model_version': self.model_version,
            'error': abs(self.predicted_weight - self.actual_weight) if self.actual_weight else None
        }
