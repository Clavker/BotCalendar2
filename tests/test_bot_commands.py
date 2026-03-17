import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, time


# Все тесты команд бота используют моки, Django не нужен
@pytest.mark.unit
@pytest.mark.asyncio
class TestBotCommands:
    async def test_start_command(self):
        """Тест команды /start"""
        # Создаём мок сообщения
        mock_message = AsyncMock()
        mock_message.from_user.first_name = "Test"
        mock_message.answer = AsyncMock()

        # Импортируем и вызываем хендлер
        from bot import cmd_start
        await cmd_start(mock_message)

        # Проверяем, что ответ был отправлен
        mock_message.answer.assert_called_once()
        args, _ = mock_message.answer.call_args
        assert "Привет" in args[0]

    async def test_register_command_new_user(self):
        """Тест регистрации нового пользователя"""
        mock_message = AsyncMock()
        mock_message.from_user.id = 12345
        mock_message.from_user.username = "testuser"
        mock_message.from_user.first_name = "Test"
        mock_message.from_user.last_name = "User"
        mock_message.answer = AsyncMock()

        with patch('bot.get_or_create_profile') as mock_get_profile, \
                patch('bot.increment_user_count') as mock_inc:
            # Имитируем создание нового профиля
            mock_profile = MagicMock()
            mock_get_profile.return_value = (mock_profile, True)

            from bot import register_handler
            await register_handler(mock_message)

            # Проверяем вызовы
            mock_get_profile.assert_called_once()
            mock_inc.assert_called_once()
            mock_message.answer.assert_called_once()

    async def test_register_command_existing_user(self):
        """Тест регистрации существующего пользователя"""
        mock_message = AsyncMock()
        mock_message.from_user.id = 12345
        mock_message.from_user.first_name = "Test"
        mock_message.answer = AsyncMock()

        with patch('bot.get_or_create_profile') as mock_get_profile, \
                patch('bot.increment_user_count') as mock_inc:
            # Имитируем существующий профиль
            mock_profile = MagicMock()
            mock_get_profile.return_value = (mock_profile, False)

            from bot import register_handler
            await register_handler(mock_message)

            # Проверяем, что счётчик не увеличивался
            mock_inc.assert_not_called()
            mock_message.answer.assert_called_once()

    async def test_share_event_command(self):
        """Тест команды /share_event"""
        mock_message = AsyncMock()
        mock_message.text = "/share_event 1"
        mock_message.from_user.id = 12345
        mock_message.answer = AsyncMock()

        with patch('bot.set_event_public') as mock_set:
            mock_set.return_value = (True, "Событие теперь публичное")

            from bot import share_event_handler
            await share_event_handler(mock_message)

            mock_set.assert_called_with(12345, 1, True)
            mock_message.answer.assert_called_with(
                "✅ Событие теперь публичное")

    async def test_unshare_event_command(self):
        """Тест команды /unshare_event"""
        mock_message = AsyncMock()
        mock_message.text = "/unshare_event 1"
        mock_message.from_user.id = 12345
        mock_message.answer = AsyncMock()

        with patch('bot.set_event_public') as mock_set:
            mock_set.return_value = (True, "Событие теперь приватное")

            from bot import unshare_event_handler
            await unshare_event_handler(mock_message)

            mock_set.assert_called_with(12345, 1, False)
            mock_message.answer.assert_called_with(
                "✅ Событие теперь приватное")

    async def test_share_event_invalid_id(self):
        """Тест команды /share_event с некорректным ID"""
        mock_message = AsyncMock()
        mock_message.text = "/share_event abc"  # не число
        mock_message.answer = AsyncMock()

        from bot import share_event_handler
        await share_event_handler(mock_message)

        # Должна быть ошибка о том, что ID должен быть числом
        mock_message.answer.assert_called_once()
        args, _ = mock_message.answer.call_args
        assert "числом" in args[0] or "ID" in args[0]