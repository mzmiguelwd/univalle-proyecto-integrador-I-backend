from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Task, Subtask


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['daily_limit']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name','email', 'profile']


class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = [
            'id',
            'task',
            'name',
            'target_date',
            'original_target_date',
            'estimated_hours',
            'status',
            'note',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class TaskSerializer(serializers.ModelSerializer):
    subtasks = SubtaskSerializer(many=True, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'user',
            'title',
            'task_type',
            'course',
            'due_date',
            'subtasks',
            'created_at',
            'updated_at',
            'description',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("El título no puede estar vacío.")
        return value
