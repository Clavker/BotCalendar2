import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime
from collections import defaultdict

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Импорты Django
from events.models import Event, TelegramProfile, Appointment
from django.contrib.auth.models import User

# Получаем токен из переменных окружения
API_TOKEN = os.environ.get('BOT_TOKEN')
if not API_TOKEN:
    from secrets import API_TOKEN  # fallback для локальной разработки

from appointment_utils import (
    create_appointment,
    confirm_appointment,
    cancel_appointment,
    get_user_appointments,
    is_user_free
)
from bot_stats import (
    increment_user_count,
    increment_event_count,
    increment_edited_events,
    increment_cancelled_events
)
from profile_utils import (
    get_or_create_profile,
    update_user_stats,
    get_user_calendar,
    get_user_stats,
    set_event_public,
    get_public_events_by_user,
    get_all_public_events
)

# Инициализируем бота и диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# ==================== ОБРАБОТЧИКИ ДЛЯ СОБЫТИЙ ====================

@dp.message(Command("create_event"))
async def create_event_handler(message: Message):
    """Формат: /create_event Название ГГГГ-ММ-ДД ЧЧ:ММ [описание]"""
    try:
        user_id = message.from_user.id
        args = message.text.split(maxsplit=4)

        if len(args) < 4:
            await message.answer(
                "❌ **Формат:** /create_event Название ГГГГ-ММ-ДД ЧЧ:ММ [описание]\n"
                "📌 **Пример:** /create_event Встреча 2026-12-31 15:00 Обсуждение проекта"
            )
            return

        event_name = args[1]
        date_str = args[2]
        time_str = args[3]
        event_details = args[4] if len(args) > 4 else ""

        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        event_time = datetime.strptime(time_str, "%H:%M").time()

        event = Event.objects.create(
            user=user_id,
            name=event_name,
            date=event_date,
            time=event_time,
            details=event_details,
            is_public=False
        )

        increment_event_count()
        update_user_stats(user_id, 'create')
        await message.answer(f"✅ Событие '{event_name}' создано! ID: {event.id}")

    except ValueError as e:
        await message.answer(f"❌ Неверный формат даты или времени: {e}")
    except Exception as e:
        logger.error(f"Ошибка в create_event_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при создании события: {e}")


@dp.message(Command("read_event"))
async def read_event_handler(message: Message):
    try:
        user_id = message.from_user.id
        args = message.text.split()
        if len(args) < 2:
            await message.answer("📝 Укажите ID события: /read_event 1")
            return

        event_id = int(args[1])
        try:
            event = Event.objects.get(id=event_id, user=user_id)
            response = (
                f"📅 **Событие #{event.id}**\n"
                f"📌 **Название:** {event.name}\n"
                f"📆 **Дата:** {event.date}\n"
                f"⏰ **Время:** {event.time}\n"
                f"📝 **Детали:** {event.details}"
            )
            await message.answer(response)
        except Event.DoesNotExist:
            await message.answer(f"❌ Событие с ID {event_id} не найдено или не принадлежит вам")
    except ValueError:
        await message.answer("❌ ID события должен быть числом")
    except Exception as e:
        logger.error(f"Ошибка в read_event_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("edit_event"))
async def edit_event_handler(message: Message):
    try:
        user_id = message.from_user.id
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

        allowed_fields = ['name', 'date', 'time', 'details']
        if field not in allowed_fields:
            await message.answer(f"❌ Допустимые поля: {', '.join(allowed_fields)}")
            return

        try:
            event = Event.objects.get(id=event_id, user=user_id)
            setattr(event, field, value)
            event.save()
            increment_edited_events()
            update_user_stats(user_id, 'edit')
            await message.answer(f"✅ Событие {event_id} обновлено")
        except Event.DoesNotExist:
            await message.answer(f"❌ Событие с ID {event_id} не найдено или не принадлежит вам")
    except ValueError:
        await message.answer("❌ ID события должен быть числом")
    except Exception as e:
        logger.error(f"Ошибка в edit_event_handler: {e}", exc_info=True)
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
        try:
            event = Event.objects.get(id=event_id, user=user_id)
            event.delete()
            increment_cancelled_events()
            update_user_stats(user_id, 'delete')
            await message.answer(f"✅ Событие {event_id} удалено")
        except Event.DoesNotExist:
            await message.answer(f"❌ Событие с ID {event_id} не найдено или не принадлежит вам")
    except ValueError:
        await message.answer("❌ ID события должен быть числом")
    except Exception as e:
        logger.error(f"Ошибка в delete_event_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("list_events"))
async def list_events_handler(message: Message):
    try:
        user_id = message.from_user.id
        events = Event.objects.filter(user=user_id).order_by('date', 'time')

        if not events:
            await message.answer("📭 Список ваших событий пуст")
            return

        response = "📋 **Ваши события:**\n\n"
        for event in events:
            public_mark = "🌐" if event.is_public else "🔒"
            response += (
                f"{public_mark} **#{event.id}** {event.name}\n"
                f"   📆 {event.date} ⏰ {event.time}\n"
                f"   📝 {event.details}\n\n"
            )

        if len(response) > 4096:
            for x in range(0, len(response), 4096):
                await message.answer(response[x:x + 4096])
        else:
            await message.answer(response)

    except Exception as e:
        logger.error(f"Ошибка в list_events_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


# ==================== ОБРАБОТЧИКИ ДЛЯ ПРОФИЛЯ И КАЛЕНДАРЯ ====================

@dp.message(Command("register"))
async def register_handler(message: Message):
    try:
        user = message.from_user
        profile, created = get_or_create_profile(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

        if created:
            increment_user_count()
            await message.answer(
                f"✅ Вы успешно зарегистрированы, {user.first_name}!\n"
                f"Теперь у вас есть личный кабинет.\n"
                f"Используйте /profile для просмотра статистики"
            )
        else:
            await message.answer(
                f"ℹ️ {user.first_name}, вы уже зарегистрированы в системе.\n"
                f"Ваш профиль: /profile"
            )
    except Exception as e:
        logger.error(f"Ошибка в register_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при регистрации: {e}")


@dp.message(Command("profile"))
async def profile_handler(message: Message):
    try:
        user_id = message.from_user.id
        stats = get_user_stats(user_id)

        if not stats:
            await message.answer(
                "❌ Вы не зарегистрированы.\n"
                "Используйте /register для создания профиля"
            )
            return

        total_events = Event.objects.filter(user=user_id).count()

        response = (
            f"👤 **Личный кабинет**\n\n"
            f"📌 **Имя:** {stats['first_name'] or 'Не указано'}\n"
            f"📌 **Username:** @{stats['username']}\n"
            f"📌 **Дата регистрации:** {stats['registered'].strftime('%d.%m.%Y')}\n\n"
            f"📊 **Статистика:**\n"
            f"   📅 Всего событий: {total_events}\n"
            f"   ✨ Создано: {stats['created']}\n"
            f"   ✏️ Отредактировано: {stats['edited']}\n"
            f"   🗑️ Удалено: {stats['deleted']}\n\n"
            f"📋 Используйте /mycalendar для просмотра календаря"
        )

        await message.answer(response)
    except Exception as e:
        logger.error(f"Ошибка в profile_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("mycalendar"))
async def mycalendar_handler(message: Message):
    try:
        user_id = message.from_user.id
        args = message.text.split()
        month = None
        year = None

        if len(args) >= 3:
            try:
                month = int(args[1])
                year = int(args[2])
            except ValueError:
                pass
        elif len(args) == 2:
            try:
                year = int(args[1])
            except ValueError:
                pass

        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year

        events = get_user_calendar(user_id, month, year)

        if not events:
            await message.answer(f"📅 Событий за {month:02d}.{year} нет")
            return

        calendar_by_day = {}
        for event in events:
            day = event.date.day
            if day not in calendar_by_day:
                calendar_by_day[day] = []
            calendar_by_day[day].append(event)

        month_names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                       'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

        response = f"📅 **Календарь: {month_names[month - 1]} {year}**\n\n"

        for day in sorted(calendar_by_day.keys()):
            response += f"**{day:02d}.{month:02d}**\n"
            for event in calendar_by_day[day]:
                public_mark = "🌐" if event.is_public else "🔒"
                response += f"   {public_mark} 🕐 {event.time.strftime('%H:%M')} - {event.name}\n"
                if event.details:
                    response += f"     📝 {event.details[:50]}{'...' if len(event.details) > 50 else ''}\n"
            response += "\n"

        if len(response) > 4096:
            for i in range(0, len(response), 4096):
                await message.answer(response[i:i + 4096])
        else:
            await message.answer(response)

    except Exception as e:
        logger.error(f"Ошибка в mycalendar_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


# ==================== КОМАНДЫ ДЛЯ ПУБЛИЧНЫХ СОБЫТИЙ ====================

@dp.message(Command("share_event"))
async def share_event_handler(message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer("❌ Формат: /share_event ID")
            return

        user_id = message.from_user.id
        event_id = int(args[1])

        success, msg = set_event_public(user_id, event_id, True)
        await message.answer(f"{'✅' if success else '❌'} {msg}")
    except ValueError:
        await message.answer("❌ ID должен быть числом")
    except Exception as e:
        logger.error(f"Ошибка в share_event_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("unshare_event"))
async def unshare_event_handler(message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer("❌ Формат: /unshare_event ID")
            return

        user_id = message.from_user.id
        event_id = int(args[1])

        success, msg = set_event_public(user_id, event_id, False)
        await message.answer(f"{'✅' if success else '❌'} {msg}")
    except ValueError:
        await message.answer("❌ ID должен быть числом")
    except Exception as e:
        logger.error(f"Ошибка в unshare_event_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("public"))
async def public_events_handler(message: Message):
    try:
        args = message.text.split()
        user_id = message.from_user.id

        if len(args) == 1:
            events = get_all_public_events()
            title = "📢 **Все публичные события:**"
        else:
            target_username = args[1].lstrip('@')
            try:
                target_user = User.objects.get(username=target_username)
                profile = TelegramProfile.objects.get(user=target_user)
                target_tg_id = profile.telegram_id

                events = get_public_events_by_user(target_tg_id, user_id)
                title = f"📢 **Публичные события @{target_username}:**"
            except (User.DoesNotExist, TelegramProfile.DoesNotExist):
                await message.answer(f"❌ Пользователь @{target_username} не найден")
                return

        if not events:
            await message.answer("📭 Нет публичных событий")
            return

        by_user = defaultdict(list)
        for event in events:
            try:
                profile = TelegramProfile.objects.get(telegram_id=event.user)
                owner_name = f"@{profile.telegram_username}" if profile.telegram_username else str(event.user)
            except Exception as e:
                logger.error(f"Не удалось получить профиль для user_id={event.user}: {e}")
                owner_name = str(event.user)
            by_user[owner_name].append(event)

        response = f"{title}\n\n"

        for owner, user_events in by_user.items():
            response += f"**{owner}:**\n"
            for event in user_events:
                response += (
                    f"   📅 #{event.id} {event.name}\n"
                    f"      📆 {event.date} ⏰ {event.time}\n"
                )
                if event.details:
                    response += f"      📝 {event.details[:50]}{'...' if len(event.details) > 50 else ''}\n"
            response += "\n"

        if len(response) > 4096:
            for i in range(0, len(response), 4096):
                await message.answer(response[i:i + 4096])
        else:
            await message.answer(response)

    except Exception as e:
        logger.error(f"Ошибка в public_events_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


# ==================== ОБРАБОТЧИКИ ДЛЯ ВСТРЕЧ ====================

@dp.message(Command("appointments"))
async def list_appointments_handler(message: Message):
    try:
        user_id = message.from_user.id
        appointments = get_user_appointments(user_id)

        if not appointments:
            await message.answer("📭 У вас нет встреч")
            return

        response = "📅 **Ваши встречи:**\n\n"
        for apt in appointments:
            status_emoji = {
                'pending': '⏳',
                'confirmed': '✅',
                'cancelled': '❌'
            }.get(apt.status, '❓')

            response += (
                f"{status_emoji} **#{apt.id}**\n"
                f"   📌 Событие: {apt.event.name}\n"
                f"   📆 {apt.date} ⏰ {apt.time}\n"
                f"   👤 Организатор: {apt.organizer.username}\n"
                f"   👥 Участник: {apt.participant.username}\n"
                f"   📊 Статус: {apt.get_status_display()}\n"
                f"   📝 {apt.details}\n\n"
            )

        if len(response) > 4096:
            for x in range(0, len(response), 4096):
                await message.answer(response[x:x + 4096])
        else:
            await message.answer(response)
    except Exception as e:
        logger.error(f"Ошибка в list_appointments_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("invite"))
async def invite_handler(message: Message):
    try:
        args = message.text.split(maxsplit=5)
        if len(args) < 5:
            await message.answer(
                "❌ **Формат:** /invite @username event_id ГГГГ-ММ-ДД ЧЧ:ММ [описание]\n"
                "📌 **Пример:** /invite @john 1 2026-03-20 15:00 Обсуждение проекта"
            )
            return

        username = args[1].lstrip('@')
        event_id = int(args[2])
        date_str = args[3]
        time_str = args[4]
        details = args[5] if len(args) > 5 else ""

        appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        appointment_time = datetime.strptime(time_str, "%H:%M").time()

        try:
            participant = User.objects.get(username=username)
        except User.DoesNotExist:
            await message.answer(f"❌ Пользователь @{username} не найден в системе")
            return

        success, msg, appointment = create_appointment(
            organizer_id=message.from_user.id,
            participant_id=participant.id,
            event_id=event_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            details=details
        )

        if success:
            await message.answer(
                f"✅ {msg}\n"
                f"📌 ID встречи: {appointment.id}\n"
                f"👤 Участник: @{participant.username}\n"
                f"📆 {appointment_date} ⏰ {appointment_time}"
            )

            try:
                participant_profile = TelegramProfile.objects.get(user=participant)
                await bot.send_message(
                    participant_profile.telegram_id,
                    f"📅 **Новое приглашение!**\n\n"
                    f"👤 Организатор: @{message.from_user.username}\n"
                    f"📌 Событие: {appointment.event.name}\n"
                    f"📆 Дата: {appointment_date}\n"
                    f"⏰ Время: {appointment_time}\n"
                    f"📝 Детали: {details}\n\n"
                    f"Для подтверждения: /confirm {appointment.id}\n"
                    f"Для отмены: /cancel_appointment {appointment.id}"
                )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление участнику: {e}")
        else:
            await message.answer(f"❌ {msg}")

    except ValueError as e:
        await message.answer(f"❌ Неверный формат даты или времени: {e}")
    except Exception as e:
        logger.error(f"Ошибка в invite_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("confirm"))
async def confirm_handler(message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer("❌ Формат: /confirm ID")
            return

        appointment_id = int(args[1])
        user_id = message.from_user.id
        success, msg = confirm_appointment(appointment_id, user_id)

        if success:
            appointment = Appointment.objects.get(id=appointment_id)
            organizer_profile = TelegramProfile.objects.get(user=appointment.organizer)

            await bot.send_message(
                organizer_profile.telegram_id,
                f"✅ Пользователь @{message.from_user.username} подтвердил встречу!\n"
                f"📌 Событие: {appointment.event.name}\n"
                f"📆 {appointment.date} ⏰ {appointment.time}"
            )

        await message.answer(f"{msg}")
    except ValueError:
        await message.answer("❌ ID должен быть числом")
    except Exception as e:
        logger.error(f"Ошибка в confirm_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("cancel_appointment"))
async def cancel_appointment_handler(message: Message):
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer("❌ Формат: /cancel_appointment ID")
            return

        appointment_id = int(args[1])
        user_id = message.from_user.id
        success, msg = cancel_appointment(appointment_id, user_id)

        if success:
            appointment = Appointment.objects.get(id=appointment_id)
            organizer_profile = TelegramProfile.objects.get(user=appointment.organizer)

            await bot.send_message(
                organizer_profile.telegram_id,
                f"❌ Пользователь @{message.from_user.username} отменил встречу.\n"
                f"📌 Событие: {appointment.event.name}\n"
                f"📆 {appointment.date} ⏰ {appointment.time}"
            )

        await message.answer(f"{msg}")
    except ValueError:
        await message.answer("❌ ID должен быть числом")
    except Exception as e:
        logger.error(f"Ошибка в cancel_appointment_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("free"))
async def check_free_handler(message: Message):
    try:
        args = message.text.split()
        if len(args) != 4:
            await message.answer("❌ Формат: /free @username ГГГГ-ММ-ДД ЧЧ:ММ")
            return

        username = args[1].lstrip('@')
        date_str = args[2]
        time_str = args[3]

        check_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        check_time = datetime.strptime(time_str, "%H:%M").time()

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            await message.answer(f"❌ Пользователь @{username} не найден")
            return

        if is_user_free(user.id, check_date, check_time):
            await message.answer(f"✅ @{username} свободен {date_str} в {time_str}")
        else:
            await message.answer(f"❌ @{username} занят {date_str} в {time_str}")

    except ValueError as e:
        await message.answer(f"❌ Неверный формат даты или времени: {e}")
    except Exception as e:
        logger.error(f"Ошибка в check_free_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user

    # Автоматическая регистрация пользователя
    profile, created = get_or_create_profile(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    if created:
        increment_user_count()
        await message.answer(
            f"👋 Привет, {user.first_name}! Я бот-календарь.\n\n"
            f"✅ Вы автоматически зарегистрированы в системе!\n"
            f"Теперь у вас есть личный кабинет.\n\n"
            f"📅 **Доступные команды:**\n"
            f"/profile - личный кабинет\n"
            f"/mycalendar - мой календарь\n\n"
            f"📋 **События:**\n"
            f"/create_event - создать событие\n"
            f"/list_events - список моих событий\n"
            f"/share_event ID - сделать событие публичным\n"
            f"/unshare_event ID - сделать событие приватным\n"
            f"/public - все публичные события\n"
            f"/public @user - публичные события пользователя\n\n"
            f"👥 **Встречи:**\n"
            f"/invite @user event_id ГГГГ-ММ-ДД ЧЧ:ММ - пригласить\n"
            f"/appointments - мои встречи\n"
            f"/confirm ID - подтвердить встречу\n"
            f"/cancel_appointment ID - отменить встречу\n"
            f"/free @user ГГГГ-ММ-ДД ЧЧ:ММ - проверить занятость\n\n"
            f"🔒 - личное событие, 🌐 - публичное"
        )
    else:
        await message.answer(
            f"👋 С возвращением, {user.first_name}! Я бот-календарь.\n\n"
            f"📅 **Доступные команды:**\n"
            f"/profile - личный кабинет\n"
            f"/mycalendar - мой календарь\n\n"
            f"📋 **События:**\n"
            f"/create_event - создать событие\n"
            f"/list_events - список моих событий\n"
            f"/share_event ID - сделать событие публичным\n"
            f"/unshare_event ID - сделать событие приватным\n"
            f"/public - все публичные события\n"
            f"/public @user - публичные события пользователя\n\n"
            f"👥 **Встречи:**\n"
            f"/invite @user event_id ГГГГ-ММ-ДД ЧЧ:ММ - пригласить\n"
            f"/appointments - мои встречи\n"
            f"/confirm ID - подтвердить встречу\n"
            f"/cancel_appointment ID - отменить встречу\n"
            f"/free @user ГГГГ-ММ-ДД ЧЧ:ММ - проверить занятость\n\n"
            f"🔒 - личное событие, 🌐 - публичное"
        )


# ==================== ЗАПУСК БОТА ====================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())