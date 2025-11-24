# Django equivalent of models.py
from django.db import models
from django.utils import timezone


class BodyMetrics(models.Model):
    date = models.DateTimeField(default=timezone.now)
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Body Metrics"
        ordering = ['-date']

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'weight': self.weight,
            'height': self.height
        }


class Workout(models.Model):
    date = models.DateTimeField(default=timezone.now)
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-date']

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d %H:%M'),
            'notes': self.notes,
            'exercises': [ex.to_dict() for ex in self.exercises.all()]
        }


class Exercise(models.Model):
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name='exercises'
    )
    name = models.CharField(max_length=100)
    sets = models.IntegerField()
    reps = models.IntegerField()
    weight = models.FloatField()
    rest_time = models.IntegerField(null=True, blank=True)  # rest time in seconds

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sets': self.sets,
            'reps': self.reps,
            'weight': self.weight,
            'rest_time': self.rest_time
        }