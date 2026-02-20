from django.db import models
from django.contrib.auth.models import User

# ----------------------------------
# Activity
# ----------------------------------

class Activity(models.Model):
    TYPE_CHOICES = [
        ('examen', 'Examen'),
        ('quiz', 'Quiz'),
        ('taller', 'Taller'),
        ('proyecto', 'Proyecto'),
        ('otro', 'Otro'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    course = models.CharField(max_length=100)
    event_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ----------------------------------
# Subtask
# ----------------------------------

class Subtask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('postponed', 'Postponed'),
    ]

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name='subtasks'
    )

    name = models.CharField(max_length=255)
    target_date = models.DateField()
    estimated_hours = models.FloatField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.activity.title}"


# ----------------------------------
# User Profile (Capacidad diaria)
# ----------------------------------

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    daily_limit = models.FloatField(default=6)

    def __str__(self):
        return f"Perfil de {self.user.username}"
