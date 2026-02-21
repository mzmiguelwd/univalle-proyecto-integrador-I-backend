from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import TaskViewSet, SubtaskViewSet, ProfileSettingsView, login_view, register_view


router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'subtasks', SubtaskViewSet, basename='subtask')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', login_view, name='login'),
    path('auth/register/', register_view, name='register'),
    
    # User profile endpoint
    path('profile/', ProfileSettingsView.as_view(), name='profile-settings'),
]

urlpatterns += router.urls
