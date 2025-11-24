# Django equivalent of app.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime
import json

# Assuming models are imported from the same app
# from .models import Workout, Exercise, BodyMetrics


# Template-based views (like Flask's render_template)
def index(request):
    return render(request, 'index.html')


def log_workout(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        workout = Workout.objects.create(
            date=datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
            notes=data.get('notes', '')
        )

        for ex in data.get('exercises', []):
            Exercise.objects.create(
                workout=workout,
                name=ex['name'],
                sets=int(ex['sets']),
                reps=int(ex['reps']),
                weight=float(ex['weight']),
                rest_time=int(ex.get('rest_time', 0))
            )

        return JsonResponse({'success': True, 'workout_id': workout.id})

    return render(request, 'log.html')


def history(request):
    workouts = Workout.objects.all().order_by('-date')
    return render(request, 'history.html', {'workouts': workouts})


def calendar_view(request):
    return render(request, 'calendar.html')


def progress(request):
    return render(request, 'progress.html')


def body_metrics(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        metric = BodyMetrics.objects.create(
            date=datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
            weight=float(data['weight']) if data.get('weight') else None,
            height=float(data['height']) if data.get('height') else None
        )
        return JsonResponse({'success': True})

    return render(request, 'body_metrics.html')


# API views (like Flask's jsonify)
def get_workouts(request):
    workouts = Workout.objects.all().order_by('-date')
    return JsonResponse([w.to_dict() for w in workouts], safe=False)


def get_workout(request, workout_id):
    workout = get_object_or_404(Workout, id=workout_id)
    return JsonResponse(workout.to_dict())


@require_http_methods(["DELETE"])
def delete_workout(request, workout_id):
    workout = get_object_or_404(Workout, id=workout_id)
    workout.delete()
    return JsonResponse({'success': True})


def get_exercise_progress(request, exercise_name):
    exercises = Exercise.objects.filter(
        name=exercise_name
    ).select_related('workout').order_by('workout__date')

    data = [{
        'date': ex.workout.date.strftime('%Y-%m-%d'),
        'weight': ex.weight,
        'reps': ex.reps,
        'sets': ex.sets
    } for ex in exercises]

    return JsonResponse(data, safe=False)


def get_exercise_names(request):
    exercises = Exercise.objects.values_list('name', flat=True).distinct()
    return JsonResponse(list(exercises), safe=False)


def get_body_metrics(request):
    metrics = BodyMetrics.objects.all().order_by('-date')
    return JsonResponse([m.to_dict() for m in metrics], safe=False)


def calendar_data(request):
    workouts = Workout.objects.all()
    data = {}
    for w in workouts:
        date_str = w.date.strftime('%Y-%m-%d')
        if date_str not in data:
            data[date_str] = []
        data[date_str].append({
            'id': w.id,
            'exercises': w.exercises.count(),
            'notes': w.notes
        })
    return JsonResponse(data)