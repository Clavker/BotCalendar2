# tests/unit/test_calendar_simple.py
import unittest
from unittest.mock import patch, MagicMock
from datetime import date, time
import sys
import os

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))


class TestCalendar(unittest.TestCase):
    """Тесты для класса Calendar без реальной БД"""

    def setUp(self):
        """Подготовка перед каждым тестом"""
        self.db_config = {'host': 'localhost', 'database': 'test',
                          'user': 'test', 'password': 'test'}

        # Создаём мок для psycopg2.connect
        self.mock_connect_patcher = patch('mycalendar.psycopg2.connect')
        self.mock_connect = self.mock_connect_patcher.start()

        # Настраиваем мок для курсора
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.mock_connect.return_value = self.mock_conn

        # Импортируем класс после настройки моков
        from mycalendar import Calendar
        self.calendar = Calendar(self.db_config)

    def tearDown(self):
        """Очистка после каждого теста"""
        self.mock_connect_patcher.stop()

    def test_create_event_success(self):
        """Тест успешного создания события"""
        self.mock_cursor.fetchone.return_value = [1]

        result = self.calendar.create_event(
            user_id=12345,
            event_name="Тест",
            event_date=date(2026, 12, 31),
            event_time=time(15, 30),
            event_details="Описание"
        )

        self.assertEqual(result, 1)
        self.mock_cursor.execute.assert_called_once()
        self.mock_conn.commit.assert_called_once()

    def test_read_event_found(self):
        """Тест чтения существующего события"""
        self.mock_cursor.fetchone.return_value = (1, "Тест",
                                                  date(2026, 12, 31),
                                                  time(15, 30), "Описание")

        result = self.calendar.read_event(user_id=12345, event_id=1)

        self.assertEqual(result['id'], 1)
        self.assertEqual(result['name'], "Тест")

    def test_read_event_not_found(self):
        """Тест чтения несуществующего события"""
        self.mock_cursor.fetchone.return_value = None

        result = self.calendar.read_event(user_id=12345, event_id=999)

        self.assertIsNone(result)

    def test_delete_event_success(self):
        """Тест успешного удаления события"""
        self.mock_cursor.fetchone.return_value = [1]

        result = self.calendar.delete_event(user_id=12345, event_id=1)

        self.assertEqual(result, 1)
        self.mock_conn.commit.assert_called_once()

    def test_delete_event_not_found(self):
        """Тест удаления несуществующего события"""
        self.mock_cursor.fetchone.return_value = None

        result = self.calendar.delete_event(user_id=12345, event_id=999)

        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()