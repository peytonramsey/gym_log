from django.contrib import admin
from .models import Workout, Exercise, BodyMetrics


class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 1


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ['date', 'notes']
    list_filter = ['date']
    search_fields = ['notes']
    inlines = [ExerciseInline]


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'workout', 'sets', 'reps', 'weight', 'rest_time']
    list_filter = ['name', 'workout__date']
    search_fields = ['name']


@admin.register(BodyMetrics)
class BodyMetricsAdmin(admin.ModelAdmin):
    list_display = ['date', 'weight', 'height']
    list_filter = ['date']
