from django.urls import path
from . import views

app_name = 'workouts'

urlpatterns = [
    # Template views
    path('', views.index, name='index'),
    path('log/', views.log_workout, name='log_workout'),
    path('history/', views.history, name='history'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('progress/', views.progress, name='progress'),
    path('body_metrics/', views.body_metrics, name='body_metrics'),

    # API endpoints
    path('api/workouts/', views.get_workouts, name='get_workouts'),
    path('api/workouts/<int:workout_id>/', views.get_workout, name='get_workout'),
    path('api/workouts/<int:workout_id>/', views.delete_workout, name='delete_workout'),
    path('api/progress/<str:exercise_name>/', views.get_exercise_progress, name='get_exercise_progress'),
    path('api/exercise_names/', views.get_exercise_names, name='get_exercise_names'),
    path('api/body_metrics/', views.get_body_metrics, name='get_body_metrics'),
    path('api/calendar_data/', views.calendar_data, name='calendar_data'),
]
