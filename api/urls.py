from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import LogoutView, TaskViewSet, SubtaskViewSet, ProfileSettingsView, login_view, register_view


router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'subtasks', SubtaskViewSet, basename='subtask')

urlpatterns = [
    path('auth/register/', register_view, name='register'),
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    
    path('profile/', ProfileSettingsView.as_view(), name='profile-settings'),
]

urlpatterns += router.urls
