from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Product, ProductAccess, LessonProgress, Lesson
from .serializers import ProductSerializer, LessonProgressSerializer, LessonSerializer
from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view, action
from django.contrib.auth import logout
from rest_framework import permissions
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


@api_view(['GET', 'POST'])
def register_view(request):
    """
    Представление для регистрации нового пользователя.
    Поддерживает методы: GET, POST.
    """
    if request.method == 'POST':
        username = request.data.get('username')
        password1 = request.data.get('password1')
        password2 = request.data.get('password2')

        if User.objects.filter(username=username).exists():
            return Response({"message": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)

        if password1 != password2:
            return Response({"message": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(password1)
        except ValidationError as e:
            return Response({"message": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password1)
        login(request, user)
        return Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)
    else:
        return render(request, 'register.html')


@api_view(['GET', 'POST'])
def logout_view(request):
    """
    Представление для выхода пользователя из системы.
    Поддерживает методы: GET, POST.
    """
    if request.method == 'POST':
        logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
    else:
        return render(request, 'logout.html')


@api_view(['GET', 'POST'])
def login_view(request):
    """
    Представление для входа пользователя в систему.
    Поддерживает методы: GET, POST.
    """
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return render(request, 'login.html')


class IsProductOwner(permissions.BasePermission):
    """
    Переопределение базового класса permissions.BasePermission для проверки,
    является ли текущий аутентифицированный пользователь владельцем продукта.
    """

    def has_object_permission(self, request, view, obj):
        """
        Метод для проверки, является ли пользователь владельцем продукта.
        """
        return obj.owner == request.user


class ProductViewSet(viewsets.ModelViewSet):
    """
    Представление набора данных для работы с продуктами. Только для чтения.
    Ограничивается правами доступа IsAuthenticated и IsProductOwner.
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsProductOwner]

    def get_queryset(self):
        """
        Получает набор данных продуктов, доступных для текущего аутентифицированного пользователя.
        """
        user = self.request.user
        product_ids = ProductAccess.objects.filter(user=user).values_list('product_id', flat=True)
        return Product.objects.filter(id__in=product_ids).prefetch_related('lessons')

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def create_product(self, request):
        # Сначала создаем продукт
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            owner = request.user
            product = serializer.save(owner=owner)

            # Создаем запись в ProductAccess для владельца продукта
            ProductAccess.objects.create(user=owner, product=product)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Представление набора данных для работы с уроками. Только для чтения.
    """
    serializer_class = LessonSerializer

    def get_queryset(self):
        """
        Получает набор данных уроков, связанных с продуктами, доступными для текущего аутентифицированного пользователя.
        """
        user = self.request.user
        product_ids = ProductAccess.objects.filter(user=user).values_list('product_id', flat=True)
        lesson_ids = Lesson.objects.filter(products__in=product_ids).values_list('id', flat=True)
        return Lesson.objects.filter(id__in=lesson_ids)


class LessonProgressViewSet(viewsets.ModelViewSet):
    """
    Представление набора данных для отслеживания прогресса уроков пользователей.
    Поддерживает все CRUD операции.
    """
    queryset = LessonProgress.objects.all()
    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Создает новую запись прогресса урока и обновляет статус "просмотрено", если время просмотра
        превышает 80% общей продолжительности урока.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Проверка условия для обновления статуса "просмотрено"
        lesson_progress = serializer.instance
        if lesson_progress.time_watched >= lesson_progress.lesson.duration * 0.8:
            lesson_progress.completed = True
            lesson_progress.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)