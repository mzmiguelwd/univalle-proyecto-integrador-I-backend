from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Task, Subtask, UserProfile
from .serializers import (
    TaskSerializer, 
    SubtaskSerializer, 
    UserProfileSerializer,
)

from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta


@api_view(['POST'])
def register_view(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Username y password son obligatorios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'El usuario ya existe'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create_user(username=username, email=email, password=password)
    UserProfile.objects.create(user=user)

    token = Token.objects.create(user=user)

    return Response({
        'token': token.key,
        'username': user.username,
        'message': 'Usuario registrado exitosamente'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'username': user.username,
            'user_id': user.id,
        })

    return Response(
        {'error': 'Credenciales inválidas'},
        status=status.HTTP_401_UNAUTHORIZED
    )

    login(request, user)  # 🔥 ESTO crea la cookie sessionid
    return Response({"message": "Login ok"}, status=status.HTTP_200_OK)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


    #Endpoint para tareas de hoy
    @action(detail=False, methods=["get"], url_path="today")
    def today(self, request):
        now = timezone.localtime()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        qs = self.get_queryset().filter(
            due_date__gte=start,
            due_date__lt=end
        )

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

class SubtaskViewSet(viewsets.ModelViewSet):
    serializer_class = SubtaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subtask.objects.filter(task__user=self.request.user)


class ProfileSettingsView(generics.RetrieveUpdateAPIView):
    '''
    RetrieveUpdateAPIView asegura que solo haya un endpoint GET y PATCH
    seguro, sin permitir crear perfiles duplicados ni borrar el perfil.
    '''
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
