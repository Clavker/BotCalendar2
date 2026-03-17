# test_models.py
import pytest
import django
import os
from datetime import date, time

# НАСТРОЙКА DJANGO ДЛЯ ТЕСТОВ (добавляем в САМОЕ НАЧАЛО)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calendar_admin.settings')
django.setup()

# Теперь можно импортировать модели Django
from django.contrib.auth.models import User
from events.models import Event, TelegramProfile, Appointment


@pytest.mark.django_db
class TestEventModel:
    def test_create_event(self):
        """Тест создания события"""
        event = Event.objects.create(
            user=12345,
            name='Тестовое событие',
            date=date(2026, 12, 31),
            time=time(15, 30),
            details='Тестовое описание',
            is_public=False
        )

        assert event.id is not None
        assert event.name == 'Тестовое событие'
        assert event.user == 12345
        assert str(event) == "Тестовое событие - 2026-12-31 15:30:00"

    def test_event_str_method(self):
        """Тест строкового представления"""
        event = Event.objects.create(
            user=12345,
            name='Встреча',
            date=date(2026, 12, 31),
            time=time(15, 30)
        )
        assert str(event) == "Встреча - 2026-12-31 15:30:00"


@pytest.mark.django_db
class TestTelegramProfile:
    def test_create_profile(self):
        """Тест создания профиля"""
        user = User.objects.create_user(username='testuser')
        profile = TelegramProfile.objects.create(
            user=user,
            telegram_id=12345,
            telegram_username='testuser',
            first_name='Test',
            last_name='User'
        )

        assert profile.telegram_id == 12345
        assert profile.telegram_username == 'testuser'
        assert str(profile) == '@testuser'

    def test_profile_stats_defaults(self):
        """Тест значений по умолчанию для статистики"""
        user = User.objects.create_user(username='testuser')
        profile = TelegramProfile.objects.create(
            user=user,
            telegram_id=12345
        )

        assert profile.events_created == 0
        assert profile.events_edited == 0
        assert profile.events_deleted == 0


@pytest.mark.django_db
class TestAppointmentModel:
    def test_create_appointment(self):
        """Тест создания встречи"""
        organizer = User.objects.create_user(username='organizer')
        participant = User.objects.create_user(username='participant')
        event = Event.objects.create(
            user=12345,
            name='Тест',
            date=date(2026, 12, 31),
            time=time(15, 30)
        )

        appointment = Appointment.objects.create(
            organizer=organizer,
            participant=participant,
            event=event,
            date=date(2026, 12, 31),
            time=time(16, 0),
            details='Обсуждение',
            status='pending'
        )

        assert appointment.id is not None
        assert appointment.status == 'pending'
        assert str(
            appointment) == f"{organizer.username} → {participant.username}: {event.name} (pending)"

    def test_appointment_unique_constraint(self):
        """Тест уникальности времени участника"""
        organizer = User.objects.create_user(username='organizer')
        participant = User.objects.create_user(username='participant')
        event = Event.objects.create(
            user=12345,
            name='Тест',
            date=date(2026, 12, 31),
            time=time(15, 30)
        )

        # Создаём первую встречу
        Appointment.objects.create(
            organizer=organizer,
            participant=participant,
            event=event,
            date=date(2026, 12, 31),
            time=time(16, 0),
            status='pending'
        )

        # Пытаемся создать вторую на то же время
        with pytest.raises(Exception):  # Должна быть ошибка уникальности
            Appointment.objects.create(
                organizer=organizer,
                participant=participant,
                event=event,
                date=date(2026, 12, 31),
                time=time(16, 0),
                status='confirmed'
            )