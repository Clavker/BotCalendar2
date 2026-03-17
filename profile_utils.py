# profile_utils.py
import os
import sys
import django
from datetime import datetime
from collections import defaultdict

# ==================== АВТОМАТИЧЕСКОЕ ОПРЕДЕЛЕНИЕ ПУТИ ====================
# Получаем путь к текущему файлу (profile_utils.py)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Поднимаемся на уровень выше и заходим в calendar_admin
DJANGO_PROJECT_PATH = os.path.join(CURRENT_DIR, 'calendar_admin')

# Добавляем путь в sys.path
if DJANGO_PROJECT_PATH not in sys.path:
    sys.path.insert(0, DJANGO_PROJECT_PATH)

# Устанавливаем настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calendar_admin.settings')

# Инициализируем Django
django.setup()

# ==================== ТЕПЕРЬ ИМПОРТИРУЕМ МОДЕЛИ ====================
from django.contrib.auth.models import User
from events.models import TelegramProfile, Event


# ==================== БАЗОВЫЕ ФУНКЦИИ ПРОФИЛЯ ====================

def get_or_create_profile(telegram_id, username=None, first_name=None,
                          last_name=None):
    """
    Получает или создаёт профиль пользователя.
    Возвращает (profile, created)
    """
    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
        return profile, False
    except TelegramProfile.DoesNotExist:
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
    except TelegramProfile.DoesNotExist:
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
    except TelegramProfile.DoesNotExist:
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
    except TelegramProfile.DoesNotExist:
        return None


# ==================== ФУНКЦИИ ДЛЯ ПУБЛИЧНЫХ СОБЫТИЙ ====================

def set_event_public(telegram_id, event_id, is_public=True):
    """
    Устанавливает флаг публичности события
    Возвращает (success, message)
    """
    try:
        event = Event.objects.get(id=event_id, user=telegram_id)
        event.is_public = is_public
        event.save()
        status = "публичное" if is_public else "приватное"
        return True, f"✅ Событие теперь {status}"
    except Event.DoesNotExist:
        return False, "❌ Событие не найдено или не принадлежит вам"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"


def get_public_events_by_user(target_telegram_id, requesting_user_id=None):
    """
    Возвращает публичные события пользователя target_telegram_id
    Если requesting_user_id == target_telegram_id, показывает все события
    """
    filters = {'user': target_telegram_id}

    # Если запрашивает не владелец, показываем только публичные
    if requesting_user_id != target_telegram_id:
        filters['is_public'] = True

    events = Event.objects.filter(**filters).order_by('date', 'time')
    return events


def get_all_public_events():
    """
    Возвращает все публичные события всех пользователей
    Отсортировано по дате
    """
    return Event.objects.filter(is_public=True).order_by('date', 'time')


def get_public_events_grouped_by_user(requesting_user_id=None):
    """
    Возвращает словарь: username -> список публичных событий
    Для каждого пользователя показывает только публичные события,
    кроме самого requesting_user_id (ему показывает все)
    """
    result = {}

    # Получаем всех пользователей с событиями
    all_profiles = TelegramProfile.objects.all()

    for profile in all_profiles:
        # Для владельца показываем все события
        if profile.telegram_id == requesting_user_id:
            events = Event.objects.filter(user=profile.telegram_id).order_by(
                'date', 'time')
        else:
            # Для остальных только публичные
            events = Event.objects.filter(user=profile.telegram_id,
                                          is_public=True).order_by('date',
                                                                   'time')

        if events.exists():
            display_name = profile.telegram_username or f"User_{profile.telegram_id}"
            result[display_name] = events

    return result


def get_username_by_telegram_id(telegram_id):
    """
    Возвращает username пользователя по telegram_id
    """
    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
        return profile.telegram_username or str(telegram_id)
    except TelegramProfile.DoesNotExist:
        return str(telegram_id)


# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ====================

def get_all_users():
    """
    Возвращает список всех зарегистрированных пользователей
    """
    return TelegramProfile.objects.all().order_by('-created_at')


def get_user_by_username(username):
    """
    Находит пользователя по username (без @)
    """
    try:
        # Ищем точное совпадение
        profile = TelegramProfile.objects.get(telegram_username=username)
        return profile
    except TelegramProfile.DoesNotExist:
        # Ищем частичное совпадение (без учета регистра)
        profiles = TelegramProfile.objects.filter(
            telegram_username__iexact=username)
        if profiles.exists():
            return profiles.first()
    return None


def get_user_by_telegram_id(telegram_id):
    """
    Получает профиль по telegram_id
    """
    try:
        return TelegramProfile.objects.get(telegram_id=telegram_id)
    except TelegramProfile.DoesNotExist:
        return None


# ==================== ФУНКЦИИ ДЛЯ СТАТИСТИКИ ====================

def get_global_stats():
    """
    Возвращает глобальную статистику по всем пользователям
    """
    profiles = TelegramProfile.objects.all()

    total_users = profiles.count()
    total_events_created = sum(p.events_created for p in profiles)
    total_events_edited = sum(p.events_edited for p in profiles)
    total_events_deleted = sum(p.events_deleted for p in profiles)

    # Активные сегодня (last_active сегодня)
    today = datetime.now().date()
    active_today = profiles.filter(last_active__date=today).count()

    return {
        'total_users': total_users,
        'active_today': active_today,
        'total_events_created': total_events_created,
        'total_events_edited': total_events_edited,
        'total_events_deleted': total_events_deleted,
        'total_events_all': total_events_created + total_events_edited + total_events_deleted
    }


def get_user_rank(telegram_id):
    """
    Возвращает рейтинг пользователя по количеству созданных событий
    """
    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
        # Количество пользователей, у которых больше событий
        rank = TelegramProfile.objects.filter(
            events_created__gt=profile.events_created).count() + 1
        total = TelegramProfile.objects.count()
        return rank, total
    except TelegramProfile.DoesNotExist:
        return None, None