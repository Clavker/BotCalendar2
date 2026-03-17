# tests/unit/test_notifications.py
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, time
import sys
import os

# Добавляем путь к проекту, чтобы импортировать bot
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

# Создаём правильный формат токена для тестов
VALID_TEST_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"

# Мокаем токен до импорта bot
with patch.dict('os.environ', {'BOT_TOKEN': VALID_TEST_TOKEN}):
    # Импортируем bot
    import bot


class TestNotifications(unittest.TestCase):
    """Тесты для системы уведомлений"""

    def setUp(self):
        """Подготовка перед каждым тестом"""
        # Патчим bot.bot (объект бота)
        self.patcher_bot = patch('bot.bot')
        self.mock_bot = self.patcher_bot.start()

        # Патчим функции, которые вызываются в обработчиках
        self.patcher_create = patch('bot.create_appointment')
        self.mock_create = self.patcher_create.start()

        self.patcher_confirm = patch('bot.confirm_appointment')
        self.mock_confirm = self.patcher_confirm.start()

        self.patcher_cancel = patch('bot.cancel_appointment')
        self.mock_cancel = self.patcher_cancel.start()

        # Патчим TelegramProfile.objects.get для всех тестов
        self.patcher_telegram_profile = patch(
            'events.models.TelegramProfile.objects.get')
        self.mock_telegram_profile_get = self.patcher_telegram_profile.start()

    def tearDown(self):
        """Очистка после каждого теста"""
        self.patcher_bot.stop()
        self.patcher_create.stop()
        self.patcher_confirm.stop()
        self.patcher_cancel.stop()
        self.patcher_telegram_profile.stop()

    async def async_test_invite_sends_notification(self):
        """Асинхронный тест отправки уведомления при приглашении"""
        # Создаём мок сообщения
        mock_message = AsyncMock()
        mock_message.text = "/invite @testuser 1 2026-12-31 15:30 Обсуждение"
        mock_message.from_user.id = 111
        mock_message.from_user.username = "organizer"
        mock_message.answer = AsyncMock()

        # Настраиваем мок для create_appointment
        mock_appointment = MagicMock()
        mock_appointment.id = 1
        mock_appointment.event.name = "Тестовое событие"
        self.mock_create.return_value = (True, "Приглашение отправлено",
                                         mock_appointment)

        # Патчим User.objects.get
        with patch(
                'django.contrib.auth.models.User.objects.get') as mock_user_get:
            mock_participant = MagicMock()
            mock_participant.id = 222
            mock_participant.username = "testuser"
            mock_user_get.return_value = mock_participant

            # Патчим TelegramProfile.objects.get для получения профиля участника
            mock_participant_profile = MagicMock()
            mock_participant_profile.telegram_id = 222
            self.mock_telegram_profile_get.return_value = mock_participant_profile

            # Импортируем и вызываем обработчик
            from bot import invite_handler
            await invite_handler(mock_message)

            # Проверяем, что бот отправил уведомление участнику
            self.mock_bot.send_message.assert_called_once()
            call_args = self.mock_bot.send_message.call_args
            self.assertEqual(call_args[0][0], 222)  # participant_id
            self.assertIn("Новое приглашение",
                          call_args[0][1])  # текст уведомления

    def test_invite_sends_notification(self):
        """Обёртка для запуска асинхронного теста"""
        import asyncio
        asyncio.run(self.async_test_invite_sends_notification())

    async def async_test_confirm_sends_notification(self):
        """Тест уведомления при подтверждении встречи"""
        mock_message = AsyncMock()
        mock_message.text = "/confirm 1"
        mock_message.from_user.id = 222
        mock_message.from_user.username = "participant"
        mock_message.answer = AsyncMock()

        # Настраиваем мок для confirm_appointment
        self.mock_confirm.return_value = (True, "Встреча подтверждена")

        # Патчим Appointment.objects.get для получения информации о встрече
        with patch(
                'events.models.Appointment.objects.get') as mock_appointment_get:
            mock_appointment = MagicMock()
            mock_appointment.organizer.id = 111
            mock_appointment.event.name = "Тестовое событие"
            mock_appointment_get.return_value = mock_appointment

            # Патчим TelegramProfile.objects.get для организатора
            mock_organizer_profile = MagicMock()
            mock_organizer_profile.telegram_id = 111
            self.mock_telegram_profile_get.return_value = mock_organizer_profile

            from bot import confirm_handler
            await confirm_handler(mock_message)

            # Проверяем, что уведомление организатору отправлено
            self.mock_bot.send_message.assert_called_once()
            call_args = self.mock_bot.send_message.call_args
            self.assertEqual(call_args[0][0], 111)  # organizer_id
            self.assertIn("подтвердил", call_args[0][1])

    def test_confirm_sends_notification(self):
        """Обёртка для запуска асинхронного теста"""
        import asyncio
        asyncio.run(self.async_test_confirm_sends_notification())

    async def async_test_cancel_sends_notification(self):
        """Тест уведомления при отмене встречи"""
        mock_message = AsyncMock()
        mock_message.text = "/cancel_appointment 1"
        mock_message.from_user.id = 222
        mock_message.from_user.username = "participant"
        mock_message.answer = AsyncMock()

        self.mock_cancel.return_value = (True, "Встреча отменена")

        with patch(
                'events.models.Appointment.objects.get') as mock_appointment_get:
            mock_appointment = MagicMock()
            mock_appointment.organizer.id = 111
            mock_appointment.event.name = "Тестовое событие"
            mock_appointment_get.return_value = mock_appointment

            # Патчим TelegramProfile.objects.get для организатора
            mock_organizer_profile = MagicMock()
            mock_organizer_profile.telegram_id = 111
            self.mock_telegram_profile_get.return_value = mock_organizer_profile

            from bot import cancel_appointment_handler
            await cancel_appointment_handler(mock_message)

            self.mock_bot.send_message.assert_called_once()
            call_args = self.mock_bot.send_message.call_args
            self.assertEqual(call_args[0][0], 111)
            self.assertIn("отменил", call_args[0][1])

    def test_cancel_sends_notification(self):
        """Обёртка для запуска асинхронного теста"""
        import asyncio
        asyncio.run(self.async_test_cancel_sends_notification())


if __name__ == '__main__':
    unittest.main()