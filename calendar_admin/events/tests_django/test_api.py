# test_api.py
import pytest
import django
import os
from datetime import date, time

# НАСТРОЙКА DJANGO ДЛЯ ТЕСТОВ (добавляем в САМОЕ НАЧАЛО)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calendar_admin.settings')
django.setup()

# Теперь можно импортировать модели Django
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from events.models import Event, TelegramProfile


@pytest.mark.django_db
class TestEventAPI:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser')

    def test_list_events_empty(self):
        """Тест получения пустого списка событий"""
        response = self.client.get('/api/events/')
        assert response.status_code == 200
        assert response.data == []

    def test_create_event(self):
        """Тест создания события через API"""
        data = {
            'user': 12345,
            'name': 'Тест',
            'date': '2026-12-31',
            'time': '15:30:00',
            'details': 'Описание',
            'is_public': False
        }
        response = self.client.post('/api/events/', data)
        assert response.status_code == 201
        assert response.data['name'] == 'Тест'

    def test_filter_public_events(self):
        """Тест фильтрации публичных событий"""
        # Создаём приватное событие
        Event.objects.create(
            user=12345,
            name='Приватное',
            date=date(2026, 12, 31),
            time=time(15, 30),
            is_public=False
        )
        # Создаём публичное событие
        Event.objects.create(
            user=12345,
            name='Публичное',
            date=date(2026, 12, 31),
            time=time(16, 0),
            is_public=True
        )

        response = self.client.get('/api/events/?is_public=true')
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'Публичное'