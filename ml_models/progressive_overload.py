"""
Progressive Overload Prediction Model
Predicts optimal weight for next workout based on historical performance
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import json
import os


class ProgressiveOverloadPredictor:
    """
    ML Model to predict optimal weight for progressive overload

    Features:
    - Last 5 workout weights for this exercise
    - Days since last workout
    - Average weight progression rate
    - Total training volume (sets * reps * weight)
    - Rep range (higher reps = lighter weight)
    - Rest days between sessions
    - Success rate (completed vs failed sets)
    """

    def __init__(self, model_version='v1.0'):
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            min_samples_split=5,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.model_version = model_version
        self.is_trained = False

    def extract_features(self, exercise_history, exercise_name, target_sets=3, target_reps=10):
        """
        Extract features from exercise history for a specific exercise

        Args:
            exercise_history: List of dicts with exercise data
            exercise_name: Name of exercise to predict
            target_sets: Number of sets planned
            target_reps: Number of reps planned

        Returns:
            features dict, last_weight
        """
        # Filter for this specific exercise
        exercise_data = [e for e in exercise_history if e['name'].lower() == exercise_name.lower()]

        if len(exercise_data) == 0:
            # No history for this exercise - return baseline features
            return {
                'last_weight_1': 0,
                'last_weight_2': 0,
                'last_weight_3': 0,
                'last_weight_4': 0,
                'last_weight_5': 0,
                'days_since_last': 999,
                'avg_progression_rate': 0,
                'total_volume_last': 0,
                'target_reps': target_reps,
                'target_sets': target_sets,
                'success_rate': 1.0,
                'rest_days_avg': 7,
                'workout_count': 0
            }, 0

        # Sort by date (most recent first)
        exercise_data = sorted(exercise_data, key=lambda x: x['date'], reverse=True)

        # Extract last 5 weights
        weights = [e['weight'] for e in exercise_data[:5]]
        last_weights = {f'last_weight_{i+1}': weights[i] if i < len(weights) else 0
                       for i in range(5)}

        # Calculate days since last workout
        last_date = datetime.strptime(exercise_data[0]['date'], '%Y-%m-%d %H:%M')
        days_since_last = (datetime.now() - last_date).days

        # Calculate average progression rate
        if len(weights) >= 2:
            progressions = [weights[i] - weights[i+1] for i in range(len(weights)-1)]
            avg_progression_rate = np.mean(progressions)
        else:
            avg_progression_rate = 0

        # Calculate total volume from last workout
        last_ex = exercise_data[0]
        total_volume_last = last_ex['sets'] * last_ex['reps'] * last_ex['weight']

        # Calculate success rate (assuming all exercises were completed)
        # In production, this would come from user feedback
        success_rate = 1.0

        # Calculate average rest days between workouts
        if len(exercise_data) >= 2:
            dates = [datetime.strptime(e['date'], '%Y-%m-%d %H:%M') for e in exercise_data[:5]]
            rest_days = [(dates[i] - dates[i+1]).days for i in range(len(dates)-1)]
            rest_days_avg = np.mean(rest_days)
        else:
            rest_days_avg = 7

        features = {
            **last_weights,
            'days_since_last': days_since_last,
            'avg_progression_rate': avg_progression_rate,
            'total_volume_last': total_volume_last,
            'target_reps': target_reps,
            'target_sets': target_sets,
            'success_rate': success_rate,
            'rest_days_avg': rest_days_avg,
            'workout_count': len(exercise_data)
        }

        return features, weights[0] if weights else 0

    def train(self, exercise_history):
        """
        Train the model on historical exercise data

        Args:
            exercise_history: List of all exercises with their workout dates
        """
        if len(exercise_history) < 10:
            print("Not enough data to train model (need at least 10 exercises)")
            return False

        # Group by exercise name
        exercise_groups = {}
        for ex in exercise_history:
            name = ex['name'].lower()
            if name not in exercise_groups:
                exercise_groups[name] = []
            exercise_groups[name].append(ex)

        # Create training data
        X_train_list = []
        y_train_list = []

        for exercise_name, exercises in exercise_groups.items():
            if len(exercises) < 3:
                continue

            # Sort by date
            exercises = sorted(exercises, key=lambda x: x['date'])

            # Create training samples using sliding window
            for i in range(2, len(exercises)):
                history = exercises[:i]
                target = exercises[i]

                features, _ = self.extract_features(
                    history,
                    exercise_name,
                    target['sets'],
                    target['reps']
                )

                X_train_list.append(list(features.values()))
                y_train_list.append(target['weight'])

        if len(X_train_list) < 5:
            print("Not enough training samples created")
            return False

        X_train = np.array(X_train_list)
        y_train = np.array(y_train_list)

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)

        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True

        # Calculate training metrics
        train_predictions = self.model.predict(X_train_scaled)
        train_mae = np.mean(np.abs(train_predictions - y_train))
        train_mape = np.mean(np.abs((train_predictions - y_train) / y_train)) * 100

        print(f"Model trained successfully!")
        print(f"Training MAE: {train_mae:.2f} lbs")
        print(f"Training MAPE: {train_mape:.2f}%")

        return True

    def predict(self, exercise_history, exercise_name, target_sets=3, target_reps=10):
        """
        Predict optimal weight for next workout

        Args:
            exercise_history: List of all exercise data
            exercise_name: Name of exercise to predict
            target_sets: Planned sets
            target_reps: Planned reps

        Returns:
            predicted_weight, confidence_interval, features_dict
        """
        features, last_weight = self.extract_features(
            exercise_history,
            exercise_name,
            target_sets,
            target_reps
        )

        # If no trained model or no history, use simple heuristic
        if not self.is_trained or features['workout_count'] == 0:
            # For new exercises, suggest starting light
            if last_weight == 0:
                prediction = 45  # Start with 45 lbs (empty barbell or light dumbbell)
            else:
                # Simple progression: add 2.5-5 lbs if last workout was successful
                prediction = last_weight + 2.5

            confidence_lower = prediction - 5
            confidence_upper = prediction + 5

            return prediction, (confidence_lower, confidence_upper), features

        # Use trained model
        X = np.array([list(features.values())])
        X_scaled = self.scaler.transform(X)

        prediction = self.model.predict(X_scaled)[0]

        # Calculate confidence interval (±5% of prediction)
        confidence_range = prediction * 0.05
        confidence_lower = max(0, prediction - confidence_range)
        confidence_upper = prediction + confidence_range

        # Round to nearest 2.5 lbs (standard weight plate increment)
        prediction = round(prediction / 2.5) * 2.5
        confidence_lower = round(confidence_lower / 2.5) * 2.5
        confidence_upper = round(confidence_upper / 2.5) * 2.5

        return prediction, (confidence_lower, confidence_upper), features

    def save_model(self, filepath='ml_models/progressive_overload_model.pkl'):
        """Save trained model to disk"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'model_version': self.model_version,
            'is_trained': self.is_trained
        }
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"Model saved to {filepath}")

    def load_model(self, filepath='ml_models/progressive_overload_model.pkl'):
        """Load trained model from disk"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.model_version = model_data['model_version']
            self.is_trained = model_data['is_trained']
            print(f"Model loaded from {filepath}")
            return True
        except FileNotFoundError:
            print(f"No saved model found at {filepath}")
            return False
        except Exception as e:
            print(f"Error loading model: {e}")
            return False