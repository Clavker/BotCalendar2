from django.contrib import admin
from django.utils.html import format_html
from .models import Event, BotStatistics, Appointment, TelegramProfile


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Админка для управления событиями пользователей
    """
    list_display = (
        'id',
        'name',
        'user_display',
        'date',
        'time',
        'is_public',
        'event_status'
    )
    list_display_links = ('id', 'name')
    list_filter = ('date', 'is_public', 'user')
    search_fields = ('name', 'details', 'user')
    date_hierarchy = 'date'
    list_editable = ('is_public',)  # можно менять публичность прямо в списке
    list_per_page = 25

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'name', 'date', 'time')
        }),
        ('Детали', {
            'fields': ('details', 'is_public'),
            'classes': ('wide',)
        }),
    )

    def user_display(self, obj):
        """Отображает информацию о пользователе"""
        try:
            profile = TelegramProfile.objects.get(telegram_id=obj.user)
            if profile.telegram_username:
                return format_html(
                    '<span style="color: #2A9D8F;">@{}</span><br><small>ID: {}</small>',
                    profile.telegram_username, obj.user
                )
            else:
                return format_html(
                    '<span style="color: #E76F51;">ID: {}</span>',
                    obj.user
                )
        except TelegramProfile.DoesNotExist:
            return format_html(
                '<span style="color: #E9C46A;">ID: {}</span>',
                obj.user
            )

    user_display.short_description = 'Пользователь'
    user_display.admin_order_field = 'user'

    def event_status(self, obj):
        """Статус события с цветом"""
        if obj.is_public:
            return format_html(
                '<span style="color: #2A9D8F; font-weight: bold;">🌐 Публичное</span>'
            )
        else:
            return format_html(
                '<span style="color: #E76F51;">🔒 Приватное</span>'
            )

    event_status.short_description = 'Статус'
    event_status.admin_order_field = 'is_public'

    actions = ['make_public', 'make_private']

    def make_public(self, request, queryset):
        """Сделать выбранные события публичными"""
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} событий сделано публичными')

    make_public.short_description = 'Сделать публичными'

    def make_private(self, request, queryset):
        """Сделать выбранные события приватными"""
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} событий сделано приватными')

    make_private.short_description = 'Сделать приватными'


@admin.register(BotStatistics)
class BotStatisticsAdmin(admin.ModelAdmin):
    """
    Админка для общей статистики бота
    """
    list_display = ('date', 'user_count', 'event_count', 'edited_events',
                    'cancelled_events')
    list_filter = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('date',)

    fieldsets = (
        ('Дата', {
            'fields': ('date',)
        }),
        ('Статистика', {
            'fields': ('user_count', 'event_count', 'edited_events',
                       'cancelled_events'),
            'classes': ('wide',)
        }),
    )

    def has_add_permission(self, request):
        """Запрещаем добавлять записи вручную"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Запрещаем удалять записи статистики"""
        return False


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    """
    Админка для профилей пользователей Telegram
    """
    list_display = (
        'telegram_id',
        'telegram_username_display',
        'first_name',
        'last_name',
        'stats_summary',
        'events_count',
        'last_active_display',
        'view_user_events_link'
    )
    list_display_links = ('telegram_id', 'telegram_username_display')
    list_filter = ('created_at', 'last_active')
    search_fields = ('telegram_username', 'first_name', 'last_name',
                     'telegram_id')
    readonly_fields = ('telegram_id', 'created_at', 'last_active', 'user')
    list_per_page = 25

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'user',
                'telegram_id',
                'telegram_username',
                'first_name',
                'last_name'
            )
        }),
        ('Статистика пользователя', {
            'fields': (
                'events_created',
                'events_edited',
                'events_deleted'
            ),
            'classes': ('wide',)
        }),
        ('Даты', {
            'fields': ('created_at', 'last_active'),
            'classes': ('collapse',)
        }),
    )

    def telegram_username_display(self, obj):
        """Отображает username с @"""
        if obj.telegram_username:
            return format_html(
                '<span style="color: #2A9D8F; font-weight: bold;">@{}</span>',
                obj.telegram_username
            )
        return format_html(
            '<span style="color: #E76F51;">—</span>'
        )

    telegram_username_display.short_description = 'Username'

    def stats_summary(self, obj):
        """Краткая статистика пользователя"""
        total = obj.events_created + obj.events_edited + obj.events_deleted
        return format_html(
            '<span title="Создано: {} | Изменено: {} | Удалено: {}">📊 {}</span>',
            obj.events_created, obj.events_edited, obj.events_deleted, total
        )

    stats_summary.short_description = 'Активность'

    def events_count(self, obj):
        """Количество событий пользователя"""
        from .models import Event
        count = Event.objects.filter(user=obj.telegram_id).count()

        # Сколько из них публичных
        public_count = Event.objects.filter(user=obj.telegram_id,
                                            is_public=True).count()

        return format_html(
            '{} (🌐 {})',
            count, public_count
        )

    events_count.short_description = 'Событий'

    def last_active_display(self, obj):
        """Отображает время последней активности"""
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        if obj.last_active:
            diff = now - obj.last_active
            if diff < timedelta(hours=1):
                return format_html(
                    '<span style="color: #2A9D8F;">только что</span>'
                )
            elif diff < timedelta(days=1):
                hours = int(diff.total_seconds() / 3600)
                return format_html(
                    '<span style="color: #E9C46A;">{} ч назад</span>',
                    hours
                )
            else:
                days = diff.days
                return format_html(
                    '<span style="color: #E76F51;">{} д назад</span>',
                    days
                )
        return format_html(
            '<span style="color: #E76F51;">никогда</span>'
        )

    last_active_display.short_description = 'Последний раз'

    def view_user_events_link(self, obj):
        """Ссылка на события пользователя"""
        url = f"/admin/events/event/?user={obj.telegram_id}"
        count = Event.objects.filter(user=obj.telegram_id).count()
        return format_html(
            '<a href="{}" style="background: #2A9D8F; color: white; padding: 3px 10px; border-radius: 3px; text-decoration: none;">📅 {} событий</a>',
            url, count
        )

    view_user_events_link.short_description = 'События'
    view_user_events_link.allow_tags = True


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """
    Админка для встреч между пользователями
    """
    list_display = (
        'id',
        'organizer_info',
        'participant_info',
        'event_info',
        'date',
        'time',
        'status_colored'
    )
    list_display_links = ('id',)
    list_filter = ('status', 'date')
    search_fields = ('organizer__username', 'participant__username',
                     'event__name')
    date_hierarchy = 'date'
    list_per_page = 25
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Участники', {
            'fields': ('organizer', 'participant')
        }),
        ('Событие', {
            'fields': ('event',)
        }),
        ('Дата и время', {
            'fields': ('date', 'time')
        }),
        ('Детали', {
            'fields': ('details', 'status')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def organizer_info(self, obj):
        """Информация об организаторе"""
        try:
            profile = TelegramProfile.objects.get(user=obj.organizer)
            if profile.telegram_username:
                return format_html(
                    '<span style="color: #2A9D8F;">@{}</span>',
                    profile.telegram_username
                )
        except TelegramProfile.DoesNotExist:
            pass
        return obj.organizer.username

    organizer_info.short_description = 'Организатор'

    def participant_info(self, obj):
        """Информация об участнике"""
        try:
            profile = TelegramProfile.objects.get(user=obj.participant)
            if profile.telegram_username:
                return format_html(
                    '<span style="color: #2A9D8F;">@{}</span>',
                    profile.telegram_username
                )
        except TelegramProfile.DoesNotExist:
            pass
        return obj.participant.username

    participant_info.short_description = 'Участник'

    def event_info(self, obj):
        """Информация о событии"""
        return format_html(
            '{}<br><small>📅 {}</small>',
            obj.event.name,
            obj.event.date
        )

    event_info.short_description = 'Событие'

    def status_colored(self, obj):
        """Статус с цветом"""
        colors = {
            'pending': ('#E9C46A', '⏳ Ожидается'),
            'confirmed': ('#2A9D8F', '✅ Подтверждено'),
            'cancelled': ('#E76F51', '❌ Отменено'),
        }
        color, text = colors.get(obj.status, ('#999999', '❓ Неизвестно'))
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, text
        )

    status_colored.short_description = 'Статус'

    actions = ['mark_as_confirmed', 'mark_as_cancelled']

    def mark_as_confirmed(self, request, queryset):
        """Подтвердить выбранные встречи"""
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} встреч подтверждено')

    mark_as_confirmed.short_description = 'Подтвердить выбранные встречи'

    def mark_as_cancelled(self, request, queryset):
        """Отменить выбранные встречи"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} встреч отменено')

    mark_as_cancelled.short_description = 'Отменить выбранные встречи'