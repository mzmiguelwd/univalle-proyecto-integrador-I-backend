from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Task, Subtask, UserProfile
from .serializers import (
    LoginSerializer,
    TaskSerializer, 
    SubtaskSerializer, 
    UserProfileSerializer,
)
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta
from .serializers import RegisterSerializer
from django.db.models import Q, F


@extend_schema(request=RegisterSerializer)
@api_view(['POST'])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)

    # If the data is invalid, DRF automatically returns the errors in Spanish
    # that we configured, with a status of 400 Bad Request
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': 'Usuario registrado exitosamente',
            'username': user.username,
            'token': token.key
        }, status=status.HTTP_201_CREATED)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=LoginSerializer)
@api_view(['POST'])
def login_view(request):
    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        # Extract the user that the serializer has already validated
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'username': user.username,
            'user_id': user.id,
        }, status=status.HTTP_200_OK)

    # If the credentials fail, return a 400 Bad Request with the error message in Spanish
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # api/auth/tasks/dashboard/
    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        now_date = timezone.localtime().date()
        recent_date = now_date - timedelta(days=7)

        qs = self.get_queryset().filter(
            Q(is_completed=False) | 
            Q(is_completed=True, due_date__date__gte=recent_date) |
            Q(is_completed=True, updated_at__date__gte=recent_date) 
        ).order_by(F('due_date').asc(nulls_last=True))

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

class SubtaskViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    serializer_class = SubtaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subtask.objects.filter(task__user=self.request.user)


class ProfileSettingsView(generics.RetrieveUpdateAPIView):
    '''
    RetrieveUpdateAPIView asegura que solo haya un endpoint GET y PATCH
    seguro, sin permitir crear perfiles duplicados ni borrar el perfil.
    '''
    
    authentication_classes = [TokenAuthentication]
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
