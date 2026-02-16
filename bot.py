import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

from secrets import API_TOKEN
from mycalendar import Calendar

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создаем глобальный объект календаря
calendar = Calendar()


# ==================== ОБРАБОТЧИКИ ДЛЯ КАЛЕНДАРЯ ====================

@dp.message(Command("create_event"))
async def create_event_handler(message: Message):
    try:
        # В реальном приложении нужно парсить аргументы команды
        # Пока используем заглушки
        event_name = "Тестовое событие"
        event_date = "2024-12-31"
        event_time = "12:00"
        event_details = "Описание события"

        event_id = calendar.create_event(event_name, event_date, event_time,
                                         event_details)
        await message.answer(f"Событие '{event_name}' создано! ID: {event_id}")
    except Exception as e:
        await message.answer(f"Ошибка при создании события: {e}")


@dp.message(Command("read_event"))
async def read_event_handler(message: Message):
    try:
        # Ожидаем: /read_event 1
        args = message.text.split()
        if len(args) < 2:
            await message.answer("Укажите ID события: /read_event 1")
            return

        event_id = int(args[1])
        event = calendar.read_event(event_id)
        if event:
            # Формируем красивое сообщение
            response = (
                f"📅 Событие #{event['id']}\n"
                f"📌 Название: {event['name']}\n"
                f"📆 Дата: {event['date']}\n"
                f"⏰ Время: {event['time']}\n"
                f"📝 Детали: {event['details']}"
            )
            await message.answer(response)
        else:
            await message.answer(f"Событие с ID {event_id} не найдено")
    except ValueError:
        await message.answer("ID события должен быть числом")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@dp.message(Command("edit_event"))
async def edit_event_handler(message: Message):
    try:
        # Простая реализация: /edit_event 1 name "Новое название"
        args = message.text.split(maxsplit=3)
        if len(args) < 4:
            await message.answer(
                "Формат: /edit_event ID поле значение\nПример: /edit_event 1 name Новое_название")
            return

        event_id = int(args[1])
        field = args[2]
        value = args[3]

        # Преобразуем название поля для kwargs
        field_map = {
            "name": "name",
            "date": "date",
            "time": "time",
            "details": "details"
        }

        if field not in field_map:
            await message.answer("Доступные поля: name, date, time, details")
            return

        result = calendar.edit_event(event_id, **{field_map[field]: value})
        if result:
            await message.answer(f"Событие {event_id} обновлено")
        else:
            await message.answer(f"Событие с ID {event_id} не найдено")
    except ValueError:
        await message.answer("ID события должен быть числом")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@dp.message(Command("delete_event"))
async def delete_event_handler(message: Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("Укажите ID события: /delete_event 1")
            return

        event_id = int(args[1])
        result = calendar.delete_event(event_id)
        if result:
            await message.answer(f"Событие {event_id} удалено")
        else:
            await message.answer(f"Событие с ID {event_id} не найдено")
    except ValueError:
        await message.answer("ID события должен быть числом")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@dp.message(Command("list_events"))
async def list_events_handler(message: Message):
    try:
        if not calendar.events:
            await message.answer("Список событий пуст")
            return

        response = "📋 **Все события:**\n\n"
        for event_id, event in calendar.events.items():
            response += (
                f"**#{event_id}** {event['name']}\n"
                f"   📆 {event['date']} ⏰ {event['time']}\n"
                f"   📝 {event['details']}\n\n"
            )
        await message.answer(response)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот-календарь.\n\n"
        "📅 **Доступные команды:**\n"
        "/create_event - создать событие\n"
        "/read_event - прочитать событие (ID)\n"
        "/edit_event - редактировать событие\n"
        "/delete_event - удалить событие\n"
        "/list_events - список всех событий"
    )


# ==================== ЗАПУСК БОТА ====================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())