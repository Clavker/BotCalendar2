# bot_stats.py
import os
import sys
import logging
import django
from datetime import date

# Добавляем путь к проекту Django в sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DJANGO_PROJECT_PATH = os.path.join(BASE_DIR, 'calendar_admin')
sys.path.append(DJANGO_PROJECT_PATH)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calendar_admin.settings')
django.setup()

from django.core.exceptions import ObjectDoesNotExist
from events.models import BotStatistics

# Настройка логирования
logger = logging.getLogger(__name__)


def get_or_create_today_stats():
    """Получает или создаёт запись статистики за сегодня"""
    today = date.today()
    try:
        stats, created = BotStatistics.objects.get_or_create(date=today)
        if created:
            logger.info(f"Создана новая запись статистики за {today}")
        return stats
    except Exception as e:
        logger.error(f"Ошибка в get_or_create_today_stats: {e}", exc_info=True)
        return None


def increment_user_count():
    """Увеличивает счётчик пользователей на 1"""
    stats = get_or_create_today_stats()
    if stats is None:
        logger.error("Не удалось получить статистику для increment_user_count")
        return
    try:
        stats.user_count += 1
        stats.save()
        logger.info(f"Статистика обновлена: user_count = {stats.user_count}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении user_count: {e}", exc_info=True)


def increment_event_count():
    """Увеличивает счётчик созданных событий"""
    stats = get_or_create_today_stats()
    if stats is None:
        logger.error("Не удалось получить статистику для increment_event_count")
        return
    try:
        stats.event_count += 1
        stats.save()
        logger.info(f"Статистика обновлена: event_count = {stats.event_count}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении event_count: {e}", exc_info=True)


def increment_edited_events():
    """Увеличивает счётчик отредактированных событий"""
    stats = get_or_create_today_stats()
    if stats is None:
        logger.error("Не удалось получить статистику для increment_edited_events")
        return
    try:
        stats.edited_events += 1
        stats.save()
        logger.info(f"Статистика обновлена: edited_events = {stats.edited_events}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении edited_events: {e}", exc_info=True)


def increment_cancelled_events():
    """Увеличивает счётчик отменённых событий"""
    stats = get_or_create_today_stats()
    if stats is None:
        logger.error("Не удалось получить статистику для increment_cancelled_events")
        return
    try:
        stats.cancelled_events += 1
        stats.save()
        logger.info(f"Статистика обновлена: cancelled_events = {stats.cancelled_events}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении cancelled_events: {e}", exc_info=True)