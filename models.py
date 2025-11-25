from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.String(500))
    exercises = db.relationship('Exercise', backref='workout', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d %H:%M'),
            'notes': self.notes,
            'exercises': [ex.to_dict() for ex in self.exercises]
        }

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    rest_time = db.Column(db.Integer, nullable=True)  # rest time in seconds

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sets': self.sets,
            'reps': self.reps,
            'weight': self.weight,
            'rest_time': self.rest_time
        }

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    meal_type = db.Column(db.String(20))  # Breakfast, Lunch, Dinner, Snack
    notes = db.Column(db.String(200))

    # Relationship with food items
    food_items = db.relationship('FoodItem', backref='meal', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d %H:%M'),
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
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

class WorkoutTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Push Day 1", "Pull Day"
    description = db.Column(db.String(500))
    day_of_week = db.Column(db.Integer, nullable=True)  # 0=Monday, 1=Tuesday, ..., 6=Sunday, None=Unscheduled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with template exercises
    template_exercises = db.relationship('TemplateExercise', backref='template', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'day_of_week': self.day_of_week,
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
