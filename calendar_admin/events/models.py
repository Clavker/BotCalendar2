from django.db import models
from django.contrib.auth.models import User
from datetime import date


class Event(models.Model):
    """
    Модель события в календаре пользователя
    """
    user = models.IntegerField(verbose_name='Telegram ID')
    name = models.CharField(max_length=255, verbose_name='Название')
    date = models.DateField(verbose_name='Дата')
    time = models.TimeField(verbose_name='Время')
    details = models.TextField(blank=True, verbose_name='Описание')
    is_public = models.BooleanField(default=False,
                                    verbose_name='Публичное событие')

    def __str__(self):
        return f"{self.name} - {self.date} {self.time}"

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['date', 'time']


class BotStatistics(models.Model):
    """
    Общая статистика бота по дням
    """
    date = models.DateField(unique=True, verbose_name='Дата')
    user_count = models.PositiveIntegerField(default=0,
                                             verbose_name='Новых пользователей')
    event_count = models.PositiveIntegerField(default=0,
                                              verbose_name='Создано событий')
    edited_events = models.PositiveIntegerField(default=0,
                                                verbose_name='Отредактировано событий')
    cancelled_events = models.PositiveIntegerField(default=0,
                                                   verbose_name='Отменено событий')

    def __str__(self):
        return f"Статистика за {self.date}"

    class Meta:
        verbose_name = 'Статистика бота'
        verbose_name_plural = 'Статистика бота'
        ordering = ['-date']


class TelegramProfile(models.Model):
    """
    Профиль пользователя Telegram, связанный с Django User
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='telegram_profile',
        verbose_name='Пользователь Django'
    )
    telegram_id = models.IntegerField(unique=True, verbose_name='Telegram ID')
    telegram_username = models.CharField(max_length=255, blank=True, null=True,
                                         verbose_name='Username')
    first_name = models.CharField(max_length=255, blank=True, null=True,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=255, blank=True, null=True,
                                 verbose_name='Фамилия')

    # Статистика пользователя
    events_created = models.PositiveIntegerField(default=0,
                                                 verbose_name='Создано событий')
    events_edited = models.PositiveIntegerField(default=0,
                                                verbose_name='Отредактировано')
    events_deleted = models.PositiveIntegerField(default=0,
                                                 verbose_name='Удалено')

    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Дата регистрации')
    last_active = models.DateTimeField(auto_now=True,
                                       verbose_name='Последняя активность')

    def __str__(self):
        return f"@{self.telegram_username or self.telegram_id}"

    class Meta:
        verbose_name = 'Профиль Telegram'
        verbose_name_plural = 'Профили Telegram'
        ordering = ['-created_at']


class Appointment(models.Model):
    """
    Модель встречи между пользователями
    """
    STATUS_CHOICES = [
        ('pending', 'Ожидается'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
    ]

    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organized_appointments',
        verbose_name='Организатор'
    )
    participant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='participant_appointments',
        verbose_name='Участник'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        verbose_name='Событие'
    )
    date = models.DateField(verbose_name='Дата встречи')
    time = models.TimeField(verbose_name='Время встречи')
    details = models.TextField(blank=True, verbose_name='Детали')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    def __str__(self):
        return f"{self.organizer.username} → {self.participant.username}: {self.event.name} ({self.status})"

    class Meta:
        verbose_name = 'Встреча'
        verbose_name_plural = 'Встречи'
        ordering = ['date', 'time']
        unique_together = ['participant', 'date',
                           'time']  # защита от двойного бронирования