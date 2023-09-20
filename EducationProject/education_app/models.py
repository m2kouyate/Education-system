from django.db import models
from django.contrib.auth.models import User


class Lesson(models.Model):
    """
    Модель урока, содержащая информацию о каждом уроке,
    включая название, URL видео и продолжительность урока.
    """
    name = models.CharField(max_length=255)
    video_url = models.URLField()
    duration = models.PositiveIntegerField()


class Product(models.Model):
    """
    Модель продукта, которая содержит основную информацию о продукте и его владельце.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    lessons = models.ManyToManyField(Lesson, related_name='products')


class ProductAccess(models.Model):
    """
    Модель доступа к продукту, фиксирующая, какие пользователи имеют доступ к каким продуктам,
    включая дату и время создания записи о доступе.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class LessonProgress(models.Model):
    """
    Модель прогресса урока, отслеживающая прогресс пользователя по каждому уроку,
    включая просмотренное время и статус завершения, а также отношение многие ко многим с продуктами.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    time_watched = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    products = models.ManyToManyField(Product, related_name='lesson_progresses')

    class Meta:
        unique_together = (("user", "lesson"),)








