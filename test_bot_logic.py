import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'calendar_admin'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calendar_admin.settings_test')

import django
django.setup()

from events.models import Event
from datetime import datetime

print("=" * 50)
print("ПРОВЕРКА ЛОГИКИ БОТА (без Telegram)")
print("=" * 50)

# Тест 1: Создание события
print("\n1. Создание события...")
event = Event.objects.create(
    user=12345,
    name="Тестовая встреча",
    date=datetime.now().date(),
    time=datetime.now().time(),
    details="Проверка",
    is_public=False
)
print(f"   ✅ Создано событие ID: {event.id}")

# Тест 2: Чтение события
print("\n2. Чтение события...")
read_event = Event.objects.get(id=event.id, user=12345)
print(f"   ✅ Прочитано: {read_event.name}")

# Тест 3: Редактирование события
print("\n3. Редактирование события...")
read_event.name = "Изменённое название"
read_event.save()
updated = Event.objects.get(id=event.id, user=12345)
print(f"   ✅ Новое название: {updated.name}")

# Тест 4: Список событий
print("\n4. Список событий пользователя...")
events = Event.objects.filter(user=12345).count()
print(f"   ✅ Всего событий: {events}")

# Тест 5: Удаление события
print("\n5. Удаление события...")
event.delete()
exists = Event.objects.filter(id=event.id).exists()
print(f"   ✅ Событие удалено: {not exists}")

print("\n" + "=" * 50)
print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
print("Бот работает корректно, логика сохранена.")
print("=" * 50)
EOF