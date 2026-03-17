import pytest
from datetime import date, time
from unittest.mock import patch, MagicMock, AsyncMock


# Этим тестам НЕ нужна Django (все зависимости замоканы)
@pytest.mark.unit
class TestAppointmentUtils:
    def test_is_user_free_no_appointments(self):
        """Тест проверки свободного времени (нет встреч)"""
        from appointment_utils import is_user_free

        with patch(
                'appointment_utils.Appointment.objects.filter') as mock_filter:
            mock_filter.return_value.exists.return_value = False

            result = is_user_free(12345, date(2026, 12, 31), time(15, 30))
            assert result is True

    def test_is_user_free_busy(self):
        """Тест проверки занятого времени"""
        from appointment_utils import is_user_free

        with patch(
                'appointment_utils.Appointment.objects.filter') as mock_filter:
            mock_filter.return_value.exists.return_value = True

            result = is_user_free(12345, date(2026, 12, 31), time(15, 30))
            assert result is False

    def test_create_appointment_success(self):
        """Тест успешного создания встречи"""
        from appointment_utils import create_appointment

        with patch('appointment_utils.is_user_free', return_value=True), \
                patch('appointment_utils.User.objects.get') as mock_user, \
                patch('appointment_utils.Event.objects.get') as mock_event, \
                patch(
                    'appointment_utils.Appointment.objects.create') as mock_create:
            mock_user.return_value = MagicMock(id=12345, username='testuser')
            mock_event.return_value = MagicMock(id=1, name='Тест')
            mock_appointment = MagicMock(id=1)
            mock_create.return_value = mock_appointment

            success, msg, apt = create_appointment(
                organizer_id=111,
                participant_id=222,
                event_id=1,
                appointment_date=date(2026, 12, 31),
                appointment_time=time(15, 30)
            )

            assert success is True
            assert msg == "Приглашение отправлено"
            assert apt.id == 1

    def test_create_appointment_user_busy(self):
        """Тест создания встречи, когда участник занят"""
        from appointment_utils import create_appointment

        with patch('appointment_utils.is_user_free', return_value=False):
            success, msg, apt = create_appointment(
                organizer_id=111,
                participant_id=222,
                event_id=1,
                appointment_date=date(2026, 12, 31),
                appointment_time=time(15, 30)
            )

            assert success is False
            assert msg == "Участник уже занят в это время"
            assert apt is None


@pytest.mark.unit
class TestProfileUtils:
    def test_get_or_create_profile_new(self):
        """Тест создания нового профиля"""
        from profile_utils import get_or_create_profile

        with patch('profile_utils.TelegramProfile.objects.get') as mock_get, \
                patch(
                    'profile_utils.User.objects.create_user') as mock_create_user, \
                patch(
                    'profile_utils.TelegramProfile.objects.create') as mock_create_profile:
            # Имитируем, что профиль не найден
            mock_get.side_effect = Exception("Not found")

            # Создаём мок пользователя
            mock_user = MagicMock(id=1)
            mock_create_user.return_value = mock_user

            # Создаём мок профиля
            mock_profile = MagicMock()
            mock_profile.telegram_id = 12345
            mock_create_profile.return_value = mock_profile

            profile, created = get_or_create_profile(
                telegram_id=12345,
                username='testuser',
                first_name='Test',
                last_name='User'
            )

            assert created is True
            assert profile.telegram_id == 12345
            mock_create_user.assert_called_once()
            mock_create_profile.assert_called_once()

    def test_get_or_create_profile_existing(self):
        """Тест получения существующего профиля"""
        from profile_utils import get_or_create_profile

        mock_profile = MagicMock()
        mock_profile.telegram_id = 12345

        with patch('profile_utils.TelegramProfile.objects.get',
                   return_value=mock_profile):
            profile, created = get_or_create_profile(telegram_id=12345)

            assert created is False
            assert profile.telegram_id == 12345

    def test_update_user_stats_create(self):
        """Тест увеличения счётчика созданных событий"""
        from profile_utils import update_user_stats

        mock_profile = MagicMock()
        mock_profile.events_created = 5
        mock_profile.events_edited = 3
        mock_profile.events_deleted = 1

        with patch('profile_utils.TelegramProfile.objects.get',
                   return_value=mock_profile):
            result = update_user_stats(12345, 'create')

            assert result is True
            assert mock_profile.events_created == 6
            mock_profile.save.assert_called_once()

    def test_update_user_stats_edit(self):
        """Тест увеличения счётчика отредактированных событий"""
        from profile_utils import update_user_stats

        mock_profile = MagicMock()
        mock_profile.events_created = 5
        mock_profile.events_edited = 3
        mock_profile.events_deleted = 1

        with patch('profile_utils.TelegramProfile.objects.get',
                   return_value=mock_profile):
            result = update_user_stats(12345, 'edit')

            assert result is True
            assert mock_profile.events_edited == 4
            mock_profile.save.assert_called_once()

    def test_update_user_stats_delete(self):
        """Тест увеличения счётчика удалённых событий"""
        from profile_utils import update_user_stats

        mock_profile = MagicMock()
        mock_profile.events_created = 5
        mock_profile.events_edited = 3
        mock_profile.events_deleted = 1

        with patch('profile_utils.TelegramProfile.objects.get',
                   return_value=mock_profile):
            result = update_user_stats(12345, 'delete')

            assert result is True
            assert mock_profile.events_deleted == 2
            mock_profile.save.assert_called_once()

    def test_update_user_stats_profile_not_found(self):
        """Тест обновления статистики для несуществующего профиля"""
        from profile_utils import update_user_stats

        with patch('profile_utils.TelegramProfile.objects.get') as mock_get:
            mock_get.side_effect = Exception("Not found")

            result = update_user_stats(99999, 'create')

            assert result is False