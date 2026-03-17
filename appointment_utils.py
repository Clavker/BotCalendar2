# appointment_utils.py
import os
import sys
import django
from datetime import datetime

# Настройка Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DJANGO_PROJECT_PATH = os.path.join(BASE_DIR, 'calendar_admin')
sys.path.append(DJANGO_PROJECT_PATH)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calendar_admin.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import Appointment, Event


def is_user_free(user_id, appointment_date, appointment_time):
    """
    Проверяет, свободен ли пользователь в указанное время.
    Возвращает True, если свободен, иначе False.
    """
    try:
        user = User.objects.get(id=user_id)
        existing = Appointment.objects.filter(
            participant=user,
            date=appointment_date,
            time=appointment_time
        ).exclude(status='cancelled')

        return not existing.exists()
    except Exception:
        # Если пользователь не найден или другая ошибка
        return False


def create_appointment(organizer_id, participant_id, event_id,
                       appointment_date, appointment_time, details=""):
    """
    Создаёт встречу, если участник свободен.
    Возвращает (успех, сообщение, объект встречи)
    """
    try:
        organizer = User.objects.get(id=organizer_id)
        participant = User.objects.get(id=participant_id)
        event = Event.objects.get(id=event_id)

        # Проверка занятости
        if not is_user_free(participant_id, appointment_date,
                            appointment_time):
            return False, "Участник уже занят в это время", None

        appointment = Appointment.objects.create(
            organizer=organizer,
            participant=participant,
            event=event,
            date=appointment_date,
            time=appointment_time,
            details=details,
            status='pending'
        )
        return True, "Приглашение отправлено", appointment
    except Exception as e:
        return False, f"Ошибка: {e}", None


def confirm_appointment(appointment_id):
    """Подтверждает встречу"""
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.status = 'confirmed'
        appointment.save()
        return True, "Встреча подтверждена"
    except Exception:
        return False, "Встреча не найдена"


def cancel_appointment(appointment_id):
    """Отменяет встречу"""
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.status = 'cancelled'
        appointment.save()
        return True, "Встреча отменена"
    except Exception:
        return False, "Встреча не найдена"


def get_user_appointments(user_id, status=None):
    """Возвращает список встреч пользователя (как организатора или участника)"""
    try:
        user = User.objects.get(id=user_id)
        appointments = Appointment.objects.filter(
            models.Q(organizer=user) | models.Q(participant=user)
        ).order_by('date', 'time')

        if status:
            appointments = appointments.filter(status=status)

        return appointments
    except Exception:
        return []