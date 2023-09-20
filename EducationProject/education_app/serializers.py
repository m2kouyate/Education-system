from rest_framework import serializers
from .models import Product, Lesson, LessonProgress
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели пользователя Django, выбирающий только ID и имя пользователя.
    """
    class Meta:
        model = User
        fields = ['id', 'username']


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели урока, который также включает поля времени просмотра и
    завершенности, которые вычисляются динамически на основе данных о прогрессе урока.
    """
    time_watched = serializers.SerializerMethodField()
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'name', 'video_url', 'duration', 'time_watched', 'completed']

    def get_time_watched(self, obj):
        user = self.context['request'].user
        progress = LessonProgress.objects.filter(user=user, lesson=obj).first()
        return progress.time_watched if progress else 0

    def get_completed(self, obj):
        user = self.context['request'].user
        progress = LessonProgress.objects.filter(user=user, lesson=obj).first()
        return progress.completed if progress else False


class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели продукта, который включает информацию о владельце (сериализованном)
    и связанных уроках (также сериализованных).
    """
    owner = UserSerializer(read_only=True)
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'owner', 'lessons']


class LessonProgressSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели прогресса урока, включающий информацию о продуктах,
    связанных с данным прогрессом урока (сериализованных).
    """
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = LessonProgress
        fields = ['id', 'user', 'lesson', 'time_watched', 'completed', 'products']
