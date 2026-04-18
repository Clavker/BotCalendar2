cat > README.md << 'EOF'
# 📅 Telegram Bot Calendar

Telegram бот для управления личным календарём, событиями и встречами с веб-интерфейсом администратора на Django и REST API.

## 🛠 Технологический стек

- **Python 3.12** — основной язык
- **aiogram 3.x** — Telegram Bot API
- **Django 6.x** — веб-фреймворк и админка
- **Django REST Framework** — API для интеграций
- **PostgreSQL 15** — база данных
- **Docker & Docker Compose** — контейнеризация
- **Poetry** — управление зависимостями
- **pytest** — тестирование

## Функциональность

### События
- Создание, чтение, редактирование, удаление событий
- Публичные/приватные события
- Личный календарь по месяцам
- Статистика пользователя

### Встречи
- Приглашение других пользователей
- Подтверждение/отмена встреч
- Проверка занятости участника
- Уведомления в Telegram

### Личный кабинет
- Регистрация через Telegram
- Статистика активности
- Личный календарь

### Админ-панель Django
- Управление пользователями
- Управление событиями
- Управление встречами
- Статистика бота

### REST API
- Полный CRUD для событий
- Просмотр профилей
- Управление встречами
- Статистика

## Установка и запуск

### Вариант 1: Docker (рекомендуемый)

```bash
# Клонируйте репозиторий
git clone https://github.com/Clavker/BotCalendar2.git
cd BotCalendar2

# Создайте файл .env с переменными окружения
cat > .env << 'ENV'
POSTGRES_DB=botcalendar
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
BOT_TOKEN=your_telegram_bot_token
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin123
ENV

# Запустите все сервисы
docker-compose --env-file .env up --build
```

### Вариант 2: Локальная установка
```bash
# Установите зависимости через Poetry
poetry install

# Настройте PostgreSQL
# Создайте базу данных и пользователя

# Примените миграции
cd calendar_admin
python manage.py migrate
python manage.py createsuperuser

# Запустите Django сервер
python manage.py runserver

# В отдельном терминале запустите бота
cd ..
poetry run python bot.py
```

## Команды бота
```text
Команда                     Описание
/start                      Приветствие и список команд
/register                   Регистрация в системе
/profile                    Личный кабинет
/mycalendar                 Календарь по месяцам
/create_event	            Создать событие
/list_events	            Список событий
/share_event	            Сделать событие публичным
/unshare_event	            Сделать событие приватным
/public                     Все публичные события
/invite                     Пригласить на встречу
/appointments	            Мои встречи
/confirm                    Подтвердить встречу
/cancel_appointment         Отменить встречу
/free                       Проверить занятость
```

## Тестирование
```bash
# Запуск unit-тестов
poetry run pytest tests/unit -v

# Запуск тестов Django (SQLite)
DJANGO_SETTINGS_MODULE=calendar_admin.settings_test poetry run pytest calendar_admin/events/tests_django -v
```

## API Endpoints
```text
Endpoint	Метод	Описание
/api/events/            GET/POST            Список/создание событий
/api/events/{id}/       GET/PUT/DELETE      Событие
/api/events/public/     GET                 Публичные события
/api/profiles/	        GET                 Профили пользователей
/api/appointments/      GET                 Встречи
/api/statistics/        GET                 Статистика
```
Документация API доступна по адресу: /api/ (DRF Browsable API)


## Структура проекта
```text
BotCalendar2/
├── bot.py                    # Основной файл бота
├── appointment_utils.py      # Утилиты для встреч
├── profile_utils.py          # Утилиты для профилей
├── bot_stats.py              # Статистика бота
├── calendar_admin/           # Django проект
│   ├── calendar_admin/       # Настройки Django
│   └── events/               # Приложение событий
│       ├── models.py         # Модели данных
│       ├── admin.py          # Админ-панель
│       ├── api_views.py      # REST API
│       └── serializers.py    # Сериализаторы
├── tests/                    # Тесты
├── docker-compose.yml        # Docker Compose
├── Dockerfile.bot            # Dockerfile для бота
├── Dockerfile.django         # Dockerfile для Django
└── README.md                 # Этот файл
```

## Безопасность
- Все секреты хранятся в переменных окружения
- .gitignore исключает чувствительные файлы
- API защищён правами доступа (IsAuthenticatedOrReadOnly)
- Проверка владельца при редактировании/удалении событий
- Проверка прав при подтверждении/отмене встреч

## Автор
Clavker