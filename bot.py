import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

from secrets import API_TOKEN
from notes import (create_note, read_note, edit_note, delete_note,
                   display_notes, display_sorted_notes)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("create"))
async def create_note_handler(message: Message):
    try:
        # В aiogram текст сообщения лежит в message.text
        note_text = message.text
        # Временное решение: используем chat_id как имя заметки
        note_name = str(message.chat.id)
        create_note(note_text, note_name)
        await message.answer(f"Заметка {note_name} создана.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")


@dp.message(Command("read"))
async def read_note_handler(message: Message):
    try:
        # Пока используем chat_id как имя заметки для теста
        note_name = str(message.chat.id)
        read_note()  # Функция из notes.py пока не адаптирована под бота
        await message.answer(f"Чтение заметки {note_name}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command("edit"))
async def edit_note_handler(message: Message):
    try:
        note_name = str(message.chat.id)
        edit_note()  # Будет доработано
        await message.answer(f"Редактирование заметки {note_name}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command("delete"))
async def delete_note_handler(message: Message):
    try:
        note_name = str(message.chat.id)
        delete_note()  # Будет доработано
        await message.answer(f"Удаление заметки {note_name}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command("list"))
async def list_notes_handler(message: Message):
    try:
        display_notes()  # Функция из notes.py
        await message.answer("Список заметок (от короткой к длинной)")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command("sorted"))
async def sorted_notes_handler(message: Message):
    try:
        display_sorted_notes()  # Функция из notes.py
        await message.answer("Список заметок (от длинной к короткой)")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот для заметок.\n\n"
        "Доступные команды:\n"
        "/create - создать заметку\n"
        "/read - прочитать заметку\n"
        "/edit - редактировать заметку\n"
        "/delete - удалить заметку\n"
        "/list - список заметок\n"
        "/sorted - отсортированный список"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())