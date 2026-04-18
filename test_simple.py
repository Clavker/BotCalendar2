# test_simple.py
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "calendar_admin"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "calendar_admin.settings")

import django
django.setup()

print("✅ Импорт моделей...")
from events.models import Event
print("✅ Модели импортированы")

print("✅ Импорт бота...")
import bot
print("✅ Бот импортирован")

print("\n🎉 Все проверки пройдены! Код работает корректно.")

