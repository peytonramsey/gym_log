# Django REST Framework serializers (optional, for cleaner API)
# This provides automatic JSON serialization/validation

from rest_framework import serializers
# from .models import Workout, Exercise, BodyMetrics


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'sets', 'reps', 'weight', 'rest_time']


class WorkoutSerializer(serializers.ModelSerializer):
    exercises = ExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = Workout
        fields = ['id', 'date', 'notes', 'exercises']


class BodyMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyMetrics
        fields = ['id', 'date', 'weight', 'height']