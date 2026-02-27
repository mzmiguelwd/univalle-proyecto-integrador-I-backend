from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    daily_limit = models.FloatField(default=6, help_text='Número máximo de horas de estudio por día')

    def __str__(self):
        return f'Perfil de {self.user.username}'


class Task(models.Model):
    class TaskType(models.TextChoices):
        EXAMEN = 'examen', 'Examen'
        QUIZ = 'quiz', 'Quiz'
        TALLER = 'taller', 'Taller'
        PROYECTO = 'proyecto', 'Proyecto'
        OTRO = 'otro', 'Otro'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    
    task_type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.OTRO)
    course = models.CharField(max_length=100)
    due_date = models.DateTimeField(null=True, blank=True, help_text='Fecha y hora límite de entrega')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    description = models.TextField(blank=True, null=True, help_text='Descripción adicional de la tarea')

    def __str__(self):
        return f'{self.title} - {self.course}'


class Subtask(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        DONE = 'done', 'Completada'
        POSTPONED = 'postponed', 'Pospuesta'

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='subtasks'
    )
    name = models.CharField(max_length=255)
    
    target_date = models.DateField(help_text='Fecha en la que el usuario planea hacer esta subtarea')
    original_target_date = models.DateField(null=True, blank=True, help_text='Guarda la fecha original si se reprograma')
    
    estimated_hours = models.FloatField(help_text='Duración estimada para sumar a la carga del día')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    note = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['target_date', 'status']

    def __str__(self):
        return f'{self.name} ({self.get_status_display()})'
