from rest_framework.routers import DefaultRouter
from .views import ActivityViewSet, SubtaskViewSet, UserProfileViewSet, login_view
from django.urls import path

router = DefaultRouter()
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'subtasks', SubtaskViewSet, basename='subtask')
router.register(r'profile', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('login/', login_view),
]

urlpatterns += router.urls
