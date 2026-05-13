from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Q, F
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
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

@api_view(["GET"])
def progress_report(request):

    user = request.user

    # ---------- TAREAS POR MES ----------
    monthly = (
        Task.objects
        .filter(user=user)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(tasks=Count("id"))
        .order_by("month")
    )

    monthly_tasks = [
        {
            "month": item["month"].strftime("%b"),
            "tasks": item["tasks"]
        }
        for item in monthly
    ]

    # ---------- GENERAR SEMANA COMPLETA ----------
    today = datetime.today().date()
    start_week = today - timedelta(days=today.weekday())

    week_days = []
    day_names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    for i in range(7):
        day = start_week + timedelta(days=i)
        week_days.append({
            "date": day,
            "name": day_names[i],
            "tasks": 0,
            "hours": 0
        })

    # ---------- CONSULTAR SUBTAREAS DE LA SEMANA ----------
    subtasks = Subtask.objects.filter(
        task__user=user,
        target_date__gte=start_week,
        target_date__lt=start_week + timedelta(days=7)
    )

    # ---------- LLENAR LOS DATOS ----------
    for subtask in subtasks:
        for day in week_days:
            if subtask.target_date == day["date"]:
                day["tasks"] += 1
                day["hours"] += subtask.estimated_hours

    weekly_tasks = [
        {"day": d["name"], "tasks": d["tasks"]}
        for d in week_days
    ]

    hours_worked = [
        {"day": d["name"], "hours": d["hours"]}
        for d in week_days
    ]

    # ---------- KPIs ----------
    tasks_month = Task.objects.filter(user=user).count()

    tasks_week = subtasks.count()

    total_subtasks = Subtask.objects.filter(task__user=user).count()

    completed_subtasks = Subtask.objects.filter(
        task__user=user,
        status="done"
    ).count()

    completion = 0
    if total_subtasks > 0:
        completion = round((completed_subtasks / total_subtasks) * 100)

    total_hours = Subtask.objects.filter(
        task__user=user,
        status="done"
    ).aggregate(total=Sum("estimated_hours"))["total"] or 0

    return Response({
        "monthly_tasks": monthly_tasks,
        "weekly_tasks": weekly_tasks,
        "hours_worked": hours_worked,
        "kpis": {
            "tasks_month": tasks_month,
            "tasks_week": tasks_week,
            "hours": total_hours,
            "completion": completion
        }
    })

