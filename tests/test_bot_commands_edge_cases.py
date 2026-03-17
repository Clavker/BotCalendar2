import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.unit
@pytest.mark.asyncio
class TestBotCommandsEdgeCases:
    async def test_share_event_no_args(self):
        """Тест команды /share_event без аргументов"""
        mock_message = AsyncMock()
        mock_message.text = "/share_event"
        mock_message.answer = AsyncMock()

        from bot import share_event_handler
        await share_event_handler(mock_message)

        mock_message.answer.assert_called_once()
        args, _ = mock_message.answer.call_args
        assert "Укажите ID" in args[0] or "Формат" in args[0]

    async def test_public_command_no_events(self):
        """Тест команды /public когда нет публичных событий"""
        mock_message = AsyncMock()
        mock_message.text = "/public"
        mock_message.from_user.id = 12345
        mock_message.answer = AsyncMock()

        with patch('bot.get_all_public_events') as mock_get:
            mock_get.return_value = []

            from bot import public_events_handler
            await public_events_handler(mock_message)

            mock_message.answer.assert_called_with("📭 Нет публичных событий")

    async def test_invite_command_wrong_format(self):
        """Тест команды /invite с неправильным форматом"""
        mock_message = AsyncMock()
        mock_message.text = "/invite @user"  # слишком мало аргументов
        mock_message.answer = AsyncMock()

        from bot import invite_handler
        await invite_handler(mock_message)

        mock_message.answer.assert_called_once()
        args, _ = mock_message.answer.call_args
        assert "Формат" in args[0]