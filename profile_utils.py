# profile_utils.py
import os
import sys
import django
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DJANGO_PROJECT_PATH = os.path.join(BASE_DIR, 'calendar_admin')
sys.path.append(DJANGO_PROJECT_PATH)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calendar_admin.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import TelegramProfile, Event


def get_or_create_profile(telegram_id, username=None, first_name=None,
                          last_name=None):
    """
    Получает или создаёт профиль пользователя.
    Возвращает (profile, created)
    """
    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
        return profile, False
    except Exception:
        # Создаём пользователя в Django
        django_username = f"tg_{telegram_id}"
        user = User.objects.create_user(
            username=django_username,
            first_name=first_name or '',
            last_name=last_name or ''
        )

        # Создаём профиль
        profile = TelegramProfile.objects.create(
            user=user,
            telegram_id=telegram_id,
            telegram_username=username,
            first_name=first_name,
            last_name=last_name
        )
        return profile, True


def update_user_stats(telegram_id, action):
    """
    Обновляет статистику пользователя
    action: 'create', 'edit', 'delete'
    """
    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
        if action == 'create':
            profile.events_created += 1
        elif action == 'edit':
            profile.events_edited += 1
        elif action == 'delete':
            profile.events_deleted += 1
        profile.save()
        return True
    except Exception:
        return False


def get_user_calendar(telegram_id, month=None, year=None):
    """
    Возвращает события пользователя за указанный месяц/год
    """
    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)

        # Фильтр по дате
        filters = {'user': telegram_id}
        if month and year:
            filters['date__year'] = year
            filters['date__month'] = month

        events = Event.objects.filter(**filters).order_by('date', 'time')
        return events
    except Exception:
        return []


def get_user_stats(telegram_id):
    """
    Возвращает статистику пользователя
    """
    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
        return {
            'username': profile.telegram_username or str(telegram_id),
            'first_name': profile.first_name,
            'created': profile.events_created,
            'edited': profile.events_edited,
            'deleted': profile.events_deleted,
            'total': profile.events_created + profile.events_edited + profile.events_deleted,
            'registered': profile.created_at
        }
    except Exception:
        return None


# ============== НОВЫЕ ФУНКЦИИ ==============

def set_event_public(telegram_id, event_id, is_public=True):
    """
    Устанавливает флаг публичности события
    """
    try:
        from events.models import Event
        event = Event.objects.get(id=event_id, user=telegram_id)
        event.is_public = is_public
        event.save()
        return True, f"Событие теперь {'публичное' if is_public else 'приватное'}"
    except Event.DoesNotExist:
        return False, "Событие не найдено или не принадлежит вам"
    except Exception as e:
        return False, f"Ошибка: {e}"


def get_public_events_by_user(target_telegram_id, requesting_user_id=None):
    """
    Возвращает публичные события пользователя target_telegram_id
    Если requesting_user_id == target_telegram_id, показывает все события
    """
    from events.models import Event

    filters = {'user': target_telegram_id}

    # Если запрашивает не владелец, показываем только публичные
    if requesting_user_id != target_telegram_id:
        filters['is_public'] = True

    events = Event.objects.filter(**filters).order_by('date', 'time')
    return events


def get_all_public_events():
    """
    Возвращает все публичные события всех пользователей
    """
    from events.models import Event
    return Event.objects.filter(is_public=True).order_by('date', 'time')