from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from datetime import datetime

from .models import Event, TelegramProfile, Appointment
from .serializers import (
    EventSerializer,
    TelegramProfileSerializer,
    AppointmentSerializer,
    PublicEventSerializer
)


class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint для работы с событиями.
    Доступны все CRUD операции.
    """
    queryset = Event.objects.all().order_by('-date', '-time')
    serializer_class = EventSerializer

    def get_queryset(self):
        """Фильтрация событий по параметрам запроса"""
        queryset = super().get_queryset()

        # Фильтр по пользователю
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user=user_id)

        # Фильтр по дате
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)

        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        # Фильтр по публичности
        is_public = self.request.query_params.get('is_public', None)
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == 'true')

        return queryset

    @action(detail=False, methods=['get'])
    def public(self, request):
        """Только публичные события всех пользователей"""
        public_events = Event.objects.filter(is_public=True).order_by('date',
                                                                      'time')
        serializer = PublicEventSerializer(public_events, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Сделать событие публичным"""
        event = self.get_object()
        event.is_public = True
        event.save()
        return Response({'status': 'событие опубликовано'})

    @action(detail=True, methods=['post'])
    def unshare(self, request, pk=None):
        """Сделать событие приватным"""
        event = self.get_object()
        event.is_public = False
        event.save()
        return Response({'status': 'событие скрыто'})


class UserEventsView(APIView):
    """
    API endpoint для получения событий конкретного пользователя
    """

    def get(self, request, telegram_id):
        events = Event.objects.filter(user=telegram_id).order_by('date',
                                                                 'time')

        # Если запрашивает не владелец, показываем только публичные
        # (здесь нужна аутентификация, пока упрощаем)
        is_owner = request.query_params.get('as_owner',
                                            'false').lower() == 'true'

        if not is_owner:
            events = events.filter(is_public=True)

        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)


class TelegramProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint для просмотра профилей (только чтение)
    """
    queryset = TelegramProfile.objects.all().order_by('-created_at')
    serializer_class = TelegramProfileSerializer
    lookup_field = 'telegram_id'


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint для работы со встречами
    """
    queryset = Appointment.objects.all().order_by('date', 'time')
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        """Фильтр встреч по участнику или организатору"""
        queryset = super().get_queryset()

        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(
                models.Q(organizer_id=user_id) |
                models.Q(participant_id=user_id)
            )

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Подтвердить встречу"""
        appointment = self.get_object()
        appointment.status = 'confirmed'
        appointment.save()
        return Response({'status': 'встреча подтверждена'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отменить встречу"""
        appointment = self.get_object()
        appointment.status = 'cancelled'
        appointment.save()
        return Response({'status': 'встреча отменена'})


class StatisticsView(APIView):
    """
    API endpoint для получения статистики
    """

    def get(self, request):
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        stats = {
            'total_users': TelegramProfile.objects.count(),
            'total_events': Event.objects.count(),
            'public_events': Event.objects.filter(is_public=True).count(),
            'total_appointments': Appointment.objects.count(),
            'pending_appointments': Appointment.objects.filter(
                status='pending').count(),
            'stats_by_day': []
        }

        # Статистика за последние 7 дней
        for i in range(7):
            day = today - timedelta(days=i)
            day_stats = {
                'date': day,
                'new_events': Event.objects.filter(date=day).count(),
                'new_appointments': Appointment.objects.filter(
                    date=day).count(),
            }
            stats['stats_by_day'].append(day_stats)

        return Response(stats)