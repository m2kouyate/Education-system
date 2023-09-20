from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, LessonProgressViewSet, login_view, logout_view, LessonViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'lessons', LessonViewSet, basename='lessons')
router.register(r'lesson-progress', LessonProgressViewSet, basename='lessonprogress')


urlpatterns = [
    path('', include(router.urls)),
]



