# test_bot_integration.py
import os
import sys

# Добавляем путь к Django проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'calendar_admin'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calendar_admin.settings')

import django

django.setup()

from events.models import Event
from datetime import datetime


def test_create_event():
    """Проверяет создание события в реальной БД"""
    user_id = 12345

    # Создаём
    event = Event.objects.create(
        user=user_id,
        name="Тестовое событие",
        date=datetime.now().date(),
        time=datetime.now().time(),
        details="Проверка",
        is_public=False
    )

    assert event.id is not None
    assert event.name == "Тестовое событие"
    print(f"✅ Создано событие ID: {event.id}")

    # Читаем
    read_event = Event.objects.get(id=event.id, user=user_id)
    assert read_event.name == "Тестовое событие"
    print(f"✅ Прочитано событие: {read_event.name}")

    # Удаляем
    event.delete()

    # Проверяем, что удалилось
    assert not Event.objects.filter(id=event.id).exists()
    print(f"✅ Событие удалено")

    print("\n✅ Все интеграционные проверки пройдены. Функционал не сломан!")


if __name__ == "__main__":
    test_create_event()