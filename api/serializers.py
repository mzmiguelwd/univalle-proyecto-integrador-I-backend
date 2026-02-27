from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from .models import UserProfile, Task, Subtask
from django.contrib.auth import authenticate


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['daily_limit']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name','email', 'profile']


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'El correo electrónico es obligatorio.',
            'invalid': 'Por favor, introduce una dirección de correo válida.',
            'blank': 'El correo electrónico no puede estar vacío.'
        }
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        error_messages={
            'required': 'La contraseña es obligatoria.',
            'blank': 'La contraseña no puede estar vacía.'
        }
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        error_messages = {
            'username': {
                'required': 'El nombre de usuario es obligatorio.',
                'unique': 'Este nombre de usuario ya está en uso.',
                'blank': 'El nombre de usuario no puede estar vacío.'
            }
        }
    
    # Make sure that if something goes wrong during user creation, the transaction is rolled back
    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # Automatically create the associated UserProfile
        UserProfile.objects.create(user=user)
        
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        error_messages={
            'required': 'El nombre de usuario es obligatorio.',
            'blank': 'El nombre de usuario no puede estar vacío.'
        }
    )
    password = serializers.CharField(
        write_only=True, 
        style={'input_type': 'password'},
        error_messages={
            'required': 'La contraseña es obligatoria.',
            'blank': 'La contraseña no puede estar vacía.'
        }
    )
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            # Verifies whether the credentials are correct in database
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('Esta cuenta ha sido desactivada.')
            else:
                raise serializers.ValidationError('Credenciales inválidas. Verifica tu usuario y contraseña.')
        else:
            raise serializers.ValidationError('Debe incluir nombre de usuario y contraseña.')
        
        # Save the validated user for use in the view
        data['user'] = user
        return data


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
            'is_completed',
            'subtasks',
            'created_at',
            'updated_at',
            'description',
        ]
        read_only_fields = ['created_at', 'updated_at']
