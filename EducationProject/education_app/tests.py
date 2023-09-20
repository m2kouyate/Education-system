from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

from .models import ProductAccess, Product, Lesson, LessonProgress


class RegistrationTestCase(APITestCase):

    def test_registration(self):
        data = {
            "username": "testcase",
            "password1": "someverystrongpassword",
            "password2": "someverystrongpassword",
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class LogoutTestCase(APITestCase):

    def test_logout(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LoginTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_login(self):
        data = {
            "username": "testuser",
            "password": "testpassword",
        }
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ProductViewSetTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.product = Product.objects.create(name='Test Product', owner=self.user)
        ProductAccess.objects.create(user=self.user, product=self.product)
        self.other_user = User.objects.create_user(username='otheruser', password='otherpassword')

    def test_product_create_with_automatic_product_access(self):
        self.client.login(username='testuser', password='testpassword')
        data = {
            "name": "New Test Product",
        }
        response = self.client.post(reverse('product-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверка наличия записи ProductAccess для владельца
        product_id = response.data['id']
        self.assertTrue(ProductAccess.objects.filter(user=self.user, product_id=product_id).exists())

    def test_product_access_restriction(self):
        self.client.login(username='otheruser', password='otherpassword')
        response = self.client.get(reverse('product-list'))

        # Проверка отсутствия доступа к продуктам, для которых не предоставлен доступ
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Не должно быть доступных продуктов


class LessonProgressViewSetTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.lesson = Lesson.objects.create(name='Test Lesson', video_url='http://testurl.com', duration=100)

    def test_lesson_progress_create(self):
        self.client.login(username='testuser', password='testpassword')
        data = {
            "user": self.user.id,
            "lesson": self.lesson.id,
            "time_watched": 80,
        }
        response = self.client.post(reverse('lessonprogress-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class LessonViewSetTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.product = Product.objects.create(name='Test Product', owner=self.user)
        self.lesson = Lesson.objects.create(name='Test Lesson', video_url='http://testurl.com', duration=100)
        self.product.lessons.add(self.lesson)
        ProductAccess.objects.create(user=self.user, product=self.product)

    def test_lesson_list(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('lessons-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверка, что список содержит созданный урок
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Lesson')
        self.assertEqual(response.data[0]['video_url'], 'http://testurl.com')
        self.assertEqual(response.data[0]['duration'], 100)


class UserIntegrationTest(APITestCase):

    def test_registration_login_and_access(self):
        data = {
            "username": "integration_test_user",
            "password1": "strongpassword",
            "password2": "strongpassword",
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {
            "username": "integration_test_user",
            "password": "strongpassword",
        }
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('product-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
