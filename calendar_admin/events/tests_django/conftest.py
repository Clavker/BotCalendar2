import os
import sys
import pytest
from pathlib import Path
from django.conf import settings

# Добавляем путь к корню Django проекта
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calendar_admin.settings')

# Принудительно заменяем базу данных на SQLite для всех тестов
@pytest.fixture(scope='session', autouse=True)
def use_sqlite_for_tests():
    """Заменяем PostgreSQL на SQLite для тестов"""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }