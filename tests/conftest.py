import os
import sys
import pytest
from pathlib import Path

# Добавляем путь к Django проекту
BASE_DIR = Path(__file__).resolve().parent.parent
DJANGO_PROJECT_PATH = BASE_DIR / 'calendar_admin'
sys.path.insert(0, str(DJANGO_PROJECT_PATH))

# Регистрируем кастомные маркеры
def pytest_configure(config):
    """Регистрация кастомных маркеров"""
    config.addinivalue_line(
        "markers",
        "unit: Тесты, не требующие Django (с моками)"
    )
    config.addinivalue_line(
        "markers",
        "django: Тесты, требующие Django ORM"
    )

# Автоматически применяем маркеры, если нужно
def pytest_collection_modifyitems(items):
    """Автоматически добавляем маркер django_db для тестов с django в имени"""
    for item in items:
        if "django" in item.nodeid and "django_db" not in item.keywords:
            item.add_marker(pytest.mark.django_db)