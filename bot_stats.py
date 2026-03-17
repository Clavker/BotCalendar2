import os
import sys
import django
from datetime import date

# Добавляем путь к проекту Django в sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DJANGO_PROJECT_PATH = os.path.join(BASE_DIR, 'calendar_admin')
sys.path.append(DJANGO_PROJECT_PATH)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calendar_admin.settings')
django.setup()

from events.models import BotStatistics

def get_or_create_today_stats():
    """Получает или создаёт запись статистики за сегодня"""
    today = date.today()
    stats, created = BotStatistics.objects.get_or_create(date=today)
    return stats

def increment_user_count():
    """Увеличивает счётчик пользователей на 1"""
    stats = get_or_create_today_stats()
    stats.user_count += 1
    stats.save()
    print(f"✅ Статистика обновлена: user_count = {stats.user_count}")

def increment_event_count():
    """Увеличивает счётчик созданных событий"""
    stats = get_or_create_today_stats()
    stats.event_count += 1
    stats.save()
    print(f"✅ Статистика обновлена: event_count = {stats.event_count}")

def increment_edited_events():
    """Увеличивает счётчик отредактированных событий"""
    stats = get_or_create_today_stats()
    stats.edited_events += 1
    stats.save()
    print(f"✅ Статистика обновлена: edited_events = {stats.edited_events}")

def increment_cancelled_events():
    """Увеличивает счётчик отменённых событий"""
    stats = get_or_create_today_stats()
    stats.cancelled_events += 1
    stats.save()
    print(f"✅ Статистика обновлена: cancelled_events = {stats.cancelled_events}")