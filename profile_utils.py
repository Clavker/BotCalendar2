# profile_utils.py
import os
import sys
import logging
import django
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DJANGO_PROJECT_PATH = os.path.join(BASE_DIR, 'calendar_admin')
sys.path.append(DJANGO_PROJECT_PATH)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calendar_admin.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from events.models import TelegramProfile, Event

# Настройка логирования
logger = logging.getLogger(__name__)


def get_or_create_profile(telegram_id, username=None, first_name=None, last_name=None):
    """
    Получает или создаёт профиль пользователя.
    Возвращает (profile, created)
    """
    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
        return profile, False
    except ObjectDoesNotExist:
        # Создаём пользователя в Django
        django_username = f"tg_{telegram_id}"
        try:
            user = User.objects.create_user(
                username=django_username,
                first_name=first_name or '',
                last_name=last_name or ''
            )
            profile = TelegramProfile.objects.create(
                user=user,
                telegram_id=telegram_id,
                telegram_username=username,
                first_name=first_name,
                last_name=last_name
            )
            return profile, True
        except Exception as e:
            logger.error(f"Ошибка при создании профиля для tg_{telegram_id}: {e}", exc_info=True)
            return None, False
    except Exception as e:
        logger.error(f"Ошибка в get_or_create_profile: {e}", exc_info=True)
        return None, False


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
        else:
            logger.warning(f"Неизвестное действие: {action}")
            return False
        profile.save()
        return True
    except ObjectDoesNotExist:
        logger.warning(f"Профиль не найден для telegram_id={telegram_id}")
        return False
    except Exception as e:
        logger.error(f"Ошибка в update_user_stats: {e}", exc_info=True)
        return False


def get_user_calendar(telegram_id, month=None, year=None):
    """
    Возвращает события пользователя за указанный месяц/год
    """
    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
        filters = {'user': telegram_id}
        if month and year:
            filters['date__year'] = year
            filters['date__month'] = month
        events = Event.objects.filter(**filters).order_by('date', 'time')
        return events
    except ObjectDoesNotExist:
        logger.warning(f"Профиль не найден для telegram_id={telegram_id}")
        return []
    except Exception as e:
        logger.error(f"Ошибка в get_user_calendar: {e}", exc_info=True)
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
    except ObjectDoesNotExist:
        logger.warning(f"Профиль не найден для telegram_id={telegram_id}")
        return None
    except Exception as e:
        logger.error(f"Ошибка в get_user_stats: {e}", exc_info=True)
        return None


# ============== НОВЫЕ ФУНКЦИИ ==============

def set_event_public(telegram_id, event_id, is_public=True):
    """
    Устанавливает флаг публичности события
    """
    try:
        event = Event.objects.get(id=event_id, user=telegram_id)
        event.is_public = is_public
        event.save()
        return True, f"✅ Событие теперь {'публичное' if is_public else 'приватное'}"
    except ObjectDoesNotExist:
        return False, "❌ Событие не найдено или не принадлежит вам"
    except Exception as e:
        logger.error(f"Ошибка в set_event_public: {e}", exc_info=True)
        return False, f"❌ Ошибка: {e}"


def get_public_events_by_user(target_telegram_id, requesting_user_id=None):
    """
    Возвращает публичные события пользователя target_telegram_id
    Если requesting_user_id == target_telegram_id, показывает все события
    """
    try:
        filters = {'user': target_telegram_id}
        if requesting_user_id != target_telegram_id:
            filters['is_public'] = True
        events = Event.objects.filter(**filters).order_by('date', 'time')
        return events
    except Exception as e:
        logger.error(f"Ошибка в get_public_events_by_user: {e}", exc_info=True)
        return []


def get_all_public_events():
    """
    Возвращает все публичные события всех пользователей
    """
    try:
        return Event.objects.filter(is_public=True).order_by('date', 'time')
    except Exception as e:
        logger.error(f"Ошибка в get_all_public_events: {e}", exc_info=True)
        return []