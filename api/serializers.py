from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Activity, Subtask, UserProfile


# -----------------------------
# Subtask Serializer
# -----------------------------

class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = '__all__'


# -----------------------------
# Activity Serializer
# -----------------------------

class ActivitySerializer(serializers.ModelSerializer):
    subtasks = SubtaskSerializer(many=True, read_only=True)

    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ['user']


# -----------------------------
# User Profile Serializer
# -----------------------------

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['daily_limit']
