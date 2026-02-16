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

# Параметры подключения к базе данных
DB_CONFIG = {
    'host': 'localhost',
    'database': 'botcalendar',
    'user': 'postgres',
    'password': 'твой_пароль'  # ⚠️ замени на свой пароль!
}

# Создаем глобальный объект календаря с подключением к БД
calendar = Calendar(DB_CONFIG)


# ==================== ОБРАБОТЧИКИ ДЛЯ КАЛЕНДАРЯ ====================

@dp.message(Command("create_event"))
async def create_event_handler(message: Message):
    try:
        user_id = message.from_user.id
        # Пока используем заглушки, позже добавим парсинг аргументов
        event_name = "Тестовое событие"
        event_date = "2024-12-31"
        event_time = "12:00"
        event_details = "Описание события"

        event_id = calendar.create_event(user_id, event_name, event_date,
                                         event_time, event_details)
        if event_id:
            await message.answer(
                f"✅ Событие '{event_name}' создано! ID: {event_id}")
        else:
            await message.answer("❌ Не удалось создать событие")
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании события: {e}")


@dp.message(Command("read_event"))
async def read_event_handler(message: Message):
    try:
        user_id = message.from_user.id
        # Ожидаем: /read_event 1
        args = message.text.split()
        if len(args) < 2:
            await message.answer("📝 Укажите ID события: /read_event 1")
            return

        event_id = int(args[1])
        event = calendar.read_event(user_id, event_id)

        if event:
            response = (
                f"📅 **Событие #{event['id']}**\n"
                f"📌 **Название:** {event['name']}\n"
                f"📆 **Дата:** {event['date']}\n"
                f"⏰ **Время:** {event['time']}\n"
                f"📝 **Детали:** {event['details']}"
            )
            await message.answer(response)
        else:
            await message.answer(
                f"❌ Событие с ID {event_id} не найдено или не принадлежит вам")
    except ValueError:
        await message.answer("❌ ID события должен быть числом")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("edit_event"))
async def edit_event_handler(message: Message):
    try:
        user_id = message.from_user.id
        # Формат: /edit_event 1 name "Новое название"
        args = message.text.split(maxsplit=3)
        if len(args) < 4:
            await message.answer(
                "📝 **Формат:** /edit_event ID поле значение\n"
                "**Пример:** /edit_event 1 name Новое_название\n"
                "**Доступные поля:** name, date, time, details"
            )
            return

        event_id = int(args[1])
        field = args[2]
        value = args[3]

        # Проверяем допустимость поля
        allowed_fields = ['name', 'date', 'time', 'details']
        if field not in allowed_fields:
            await message.answer(
                f"❌ Допустимые поля: {', '.join(allowed_fields)}")
            return

        # Передаём поле и значение как именованные аргументы
        result = calendar.edit_event(user_id, event_id, **{field: value})

        if result:
            await message.answer(f"✅ Событие {event_id} обновлено")
        else:
            await message.answer(
                f"❌ Событие с ID {event_id} не найдено или не принадлежит вам")
    except ValueError:
        await message.answer("❌ ID события должен быть числом")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("delete_event"))
async def delete_event_handler(message: Message):
    try:
        user_id = message.from_user.id
        args = message.text.split()
        if len(args) < 2:
            await message.answer("📝 Укажите ID события: /delete_event 1")
            return

        event_id = int(args[1])
        result = calendar.delete_event(user_id, event_id)

        if result:
            await message.answer(f"✅ Событие {event_id} удалено")
        else:
            await message.answer(
                f"❌ Событие с ID {event_id} не найдено или не принадлежит вам")
    except ValueError:
        await message.answer("❌ ID события должен быть числом")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("list_events"))
async def list_events_handler(message: Message):
    try:
        user_id = message.from_user.id
        events = calendar.display_events(
            user_id)  # теперь возвращает список событий пользователя

        if not events:
            await message.answer("📭 Список ваших событий пуст")
            return

        response = "📋 **Ваши события:**\n\n"
        for event in events:
            response += (
                f"**#{event['id']}** {event['name']}\n"
                f"   📆 {event['date']} ⏰ {event['time']}\n"
                f"   📝 {event['details']}\n\n"
            )

        # Telegram ограничивает длину сообщения
        if len(response) > 4096:
            for x in range(0, len(response), 4096):
                await message.answer(response[x:x + 4096])
        else:
            await message.answer(response)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("register"))
async def register_handler(message: Message):
    try:
        user = message.from_user
        success = calendar.register_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

        if success:
            await message.answer(
                f"✅ Вы успешно зарегистрированы, {user.first_name}!\n"
                f"Теперь все ваши события будут сохраняться в вашем личном календаре."
            )
        else:
            await message.answer(
                f"ℹ️ {user.first_name}, вы уже зарегистрированы в системе.\n"
                f"Можете продолжать пользоваться ботом."
            )
    except Exception as e:
        await message.answer(f"❌ Ошибка при регистрации: {e}")


@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    await message.answer(
        f"👋 Привет, {user.first_name}! Я бот-календарь.\n\n"
        f"📅 **Доступные команды:**\n"
        f"/register - зарегистрироваться в системе\n"
        f"/create_event - создать событие\n"
        f"/read_event - прочитать событие (ID)\n"
        f"/edit_event - редактировать событие\n"
        f"/delete_event - удалить событие\n"
        f"/list_events - список ваших событий\n\n"
        f"📌 **Примеры:**\n"
        f"/read_event 1\n"
        f"/edit_event 1 name Новое_название\n"
        f"/delete_event 1\n\n"
        f"🔐 Все ваши события видны только вам!"
    )


# ==================== ЗАПУСК БОТА ====================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())