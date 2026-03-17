# tests_django/unit/test_utils_simple.py
import unittest
from unittest.mock import patch, MagicMock
from datetime import date, time
import sys
import os

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))


class TestAppointmentUtils(unittest.TestCase):
    """Тесты для appointment_utils без Django"""

    def setUp(self):
        """Подготовка перед каждым тестом"""
        # Патчим ВСЕ зависимости от Django
        self.patcher_user = patch('appointment_utils.User')
        self.mock_user = self.patcher_user.start()

        self.patcher_event = patch('appointment_utils.Event')
        self.mock_event = self.patcher_event.start()

        self.patcher_appointment = patch('appointment_utils.Appointment')
        self.mock_appointment = self.patcher_appointment.start()

    def tearDown(self):
        """Очистка после каждого теста"""
        self.patcher_user.stop()
        self.patcher_event.stop()
        self.patcher_appointment.stop()

    def test_is_user_free_no_appointments(self):
        """Тест проверки свободного времени (нет встреч)"""
        # Настраиваем мок для User.objects.get
        mock_user_instance = MagicMock()
        mock_user_instance.id = 12345
        self.mock_user.objects.get.return_value = mock_user_instance

        # Настраиваем цепочку: filter().exclude().exists()
        mock_filter = MagicMock()
        mock_exclude = MagicMock()
        mock_filter.exclude.return_value = mock_exclude
        mock_exclude.exists.return_value = False

        self.mock_appointment.objects.filter.return_value = mock_filter

        from appointment_utils import is_user_free
        result = is_user_free(12345, date(2026, 12, 31), time(15, 30))

        print(f"\nDEBUG: result = {result}")
        print(
            f"DEBUG: mock_user.objects.get called: {self.mock_user.objects.get.called}")
        print(
            f"DEBUG: mock_appointment.objects.filter called: {self.mock_appointment.objects.filter.called}")
        print(f"DEBUG: filter.exclude called: {mock_filter.exclude.called}")
        print(f"DEBUG: exclude.exists called: {mock_exclude.exists.called}")

        self.assertTrue(result)
        self.mock_user.objects.get.assert_called_once_with(id=12345)
        self.mock_appointment.objects.filter.assert_called_once()
        mock_filter.exclude.assert_called_once_with(status='cancelled')
        mock_exclude.exists.assert_called_once()

    def test_is_user_free_busy(self):
        """Тест проверки занятого времени"""
        # Настраиваем мок для User.objects.get
        mock_user_instance = MagicMock()
        mock_user_instance.id = 12345
        self.mock_user.objects.get.return_value = mock_user_instance

        # Настраиваем мок для Appointment.objects.filter
        mock_filter_result = MagicMock()
        mock_filter_result.exists.return_value = True
        self.mock_appointment.objects.filter.return_value = mock_filter_result

        from appointment_utils import is_user_free
        result = is_user_free(12345, date(2026, 12, 31), time(15, 30))

        self.assertFalse(result)
        self.mock_user.objects.get.assert_called_once_with(id=12345)
        self.mock_appointment.objects.filter.assert_called_once()

    def test_is_user_free_user_not_found(self):
        """Тест проверки для несуществующего пользователя"""
        # Настраиваем мок на исключение
        from django.contrib.auth.models import User
        self.mock_user.objects.get.side_effect = User.DoesNotExist()

        from appointment_utils import is_user_free
        result = is_user_free(99999, date(2026, 12, 31), time(15, 30))

        self.assertFalse(result)

    def test_create_appointment_user_busy(self):
        """Тест создания встречи, когда участник занят"""
        # Патчим is_user_free прямо перед вызовом
        with patch('appointment_utils.is_user_free') as mock_is_free:
            mock_is_free.return_value = False

            from appointment_utils import create_appointment
            success, msg, apt = create_appointment(
                organizer_id=111,
                participant_id=222,
                event_id=1,
                appointment_date=date(2026, 12, 31),
                appointment_time=time(15, 30),
                details=""
            )

            self.assertFalse(success)
            self.assertEqual(msg, "Участник уже занят в это время")
            self.assertIsNone(apt)
            mock_is_free.assert_called_once_with(222, date(2026, 12, 31),
                                                 time(15, 30))

    def test_create_appointment_success(self):
        """Тест успешного создания встречи"""
        # Патчим все зависимости
        with patch('appointment_utils.is_user_free', return_value=True), \
                patch('appointment_utils.User.objects.get') as mock_user_get, \
                patch('appointment_utils.Event.objects.get') as mock_event_get, \
                patch(
                    'appointment_utils.Appointment.objects.create') as mock_create:
            # Настраиваем моки
            mock_organizer = MagicMock(id=111, username='organizer')
            mock_participant = MagicMock(id=222, username='participant')
            mock_event = MagicMock(id=1, name='Тест')

            mock_user_get.side_effect = [mock_organizer, mock_participant]
            mock_event_get.return_value = mock_event

            mock_appointment = MagicMock(id=1)
            mock_create.return_value = mock_appointment

            from appointment_utils import create_appointment
            success, msg, apt = create_appointment(
                organizer_id=111,
                participant_id=222,
                event_id=1,
                appointment_date=date(2026, 12, 31),
                appointment_time=time(15, 30),
                details="Обсуждение"
            )

            self.assertTrue(success)
            self.assertEqual(msg, "Приглашение отправлено")
            self.assertEqual(apt.id, 1)


class TestProfileUtils(unittest.TestCase):
    """Тесты для profile_utils без Django"""

    def setUp(self):
        """Подготовка перед каждым тестом"""
        self.patcher_profile = patch('profile_utils.TelegramProfile')
        self.mock_profile = self.patcher_profile.start()

    def tearDown(self):
        """Очистка после каждого теста"""
        self.patcher_profile.stop()

    def test_update_user_stats_create(self):
        """Тест увеличения счётчика созданных событий"""
        mock_profile_instance = MagicMock()
        mock_profile_instance.events_created = 5
        mock_profile_instance.events_edited = 3
        mock_profile_instance.events_deleted = 1
        self.mock_profile.objects.get.return_value = mock_profile_instance

        from profile_utils import update_user_stats
        result = update_user_stats(12345, 'create')

        self.assertTrue(result)
        self.assertEqual(mock_profile_instance.events_created, 6)
        mock_profile_instance.save.assert_called_once()

    def test_update_user_stats_edit(self):
        """Тест увеличения счётчика отредактированных событий"""
        mock_profile_instance = MagicMock()
        mock_profile_instance.events_created = 5
        mock_profile_instance.events_edited = 3
        mock_profile_instance.events_deleted = 1
        self.mock_profile.objects.get.return_value = mock_profile_instance

        from profile_utils import update_user_stats
        result = update_user_stats(12345, 'edit')

        self.assertTrue(result)
        self.assertEqual(mock_profile_instance.events_edited, 4)
        mock_profile_instance.save.assert_called_once()

    def test_update_user_stats_delete(self):
        """Тест увеличения счётчика удалённых событий"""
        mock_profile_instance = MagicMock()
        mock_profile_instance.events_created = 5
        mock_profile_instance.events_edited = 3
        mock_profile_instance.events_deleted = 1
        self.mock_profile.objects.get.return_value = mock_profile_instance

        from profile_utils import update_user_stats
        result = update_user_stats(12345, 'delete')

        self.assertTrue(result)
        self.assertEqual(mock_profile_instance.events_deleted, 2)
        mock_profile_instance.save.assert_called_once()

    def test_update_user_stats_profile_not_found(self):
        """Тест обновления статистики для несуществующего профиля"""
        from events.models import TelegramProfile
        self.mock_profile.objects.get.side_effect = TelegramProfile.DoesNotExist()

        from profile_utils import update_user_stats
        result = update_user_stats(99999, 'create')

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()