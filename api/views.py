from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Q, F
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from .models import Task, Subtask
from .serializers import (
    LoginSerializer,
    TaskSerializer, 
    SubtaskSerializer, 
    UserProfileSerializer,
    RegisterSerializer,
    EmptySerializer
)


@extend_schema(
    request=RegisterSerializer,
    responses={
        201: inline_serializer(
            name='RegisterResponse',
             fields={
                 'message': serializers.CharField(),
                 'username': serializers.CharField(),
                 'token': serializers.CharField(),
             }
        ),
        400: OpenApiTypes.OBJECT,
    },
)
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


@extend_schema(
    request=LoginSerializer,
    responses={
        200: inline_serializer(
            name='LoginResponse',
             fields={
                 'token': serializers.CharField(),
                 'username': serializers.CharField(),
                 'user_id': serializers.IntegerField(),
             }
        ),
        400: inline_serializer(
            name='LoginErrorResponse',
             fields={
                 'non_field_errors': serializers.ListField(child=serializers.CharField())
            }
        )
    }
)
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


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmptySerializer
    
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({'detail': 'Sesión cerrada exitosamente'}, status=status.HTTP_200_OK)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    
    authentication_classes = [TokenAuthentication]
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # api/auth/tasks/dashboard/
    @action(detail=False, methods=['get'], url_path='dashboard')
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
    queryset = Subtask.objects.all()
    
    authentication_classes = [TokenAuthentication]
    serializer_class = SubtaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # aceptar task desde el body o desde kwargs (rutas anidadas)
        task_id = self.request.data.get('task') or self.kwargs.get('task_pk')
        if not task_id:
            raise serializers.ValidationError({'task': ['Este campo es obligatorio cuando se crea una subtarea por separado.']})

        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise serializers.ValidationError({'task': ['Tarea no encontrada.']})

        if task.user != self.request.user:
            raise permissions.PermissionDenied('No puedes crear subtareas para esa tarea.')

        # Validamos que la fecha objetivo no sea mayor que la de la tarea
        target_date = serializer.validated_data.get('target_date')
        if task.due_date and target_date:
            if target_date > task.due_date.date():
                raise serializers.ValidationError({'target_date': ['La fecha de la subtarea no puede ser posterior a la fecha límite de la tarea.']})

        serializer.save(task=task)
        
    def get_queryset(self):
        return Subtask.objects.filter(task__user=self.request.user)

    @action(detail=False, methods=['get'], url_path='workload')
    def workload(self, request):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'error': 'Parámetro date es requerido (YYYY-MM-DD)'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        subtasks = self.get_queryset().filter(target_date=target_date)
        total_hours = sum(st.estimated_hours for st in subtasks if st.estimated_hours)
        daily_limit = request.user.profile.daily_limit

        return Response({
            'date': date_str,
            'total_hours': total_hours,
            'daily_limit': daily_limit
        })


class ProfileSettingsView(generics.RetrieveUpdateAPIView):
    '''
    RetrieveUpdateAPIView asegura que solo haya un endpoint GET y PATCH
    seguro, sin permitir crear perfiles duplicados ni borrar el perfil.
    '''
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


