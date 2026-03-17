from rest_framework import serializers
from .models import Event, TelegramProfile, Appointment
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя Django"""

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class TelegramProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля Telegram"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = TelegramProfile
        fields = [
            'telegram_id',
            'telegram_username',
            'first_name',
            'last_name',
            'events_created',
            'events_edited',
            'events_deleted',
            'created_at',
            'last_active'
        ]


class EventSerializer(serializers.ModelSerializer):
    """Сериализатор для событий"""
    owner_info = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id',
            'user',
            'name',
            'date',
            'time',
            'details',
            'is_public',
            'owner_info'
        ]

    def get_owner_info(self, obj):
        """Добавляет информацию о владельце события"""
        try:
            profile = TelegramProfile.objects.get(telegram_id=obj.user)
            return {
                'username': profile.telegram_username,
                'name': f"{profile.first_name} {profile.last_name}".strip()
            }
        except TelegramProfile.DoesNotExist:
            return None


class AppointmentSerializer(serializers.ModelSerializer):
    """Сериализатор для встреч"""
    organizer_details = serializers.SerializerMethodField()
    participant_details = serializers.SerializerMethodField()
    event_details = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id',
            'organizer',
            'participant',
            'event',
            'date',
            'time',
            'details',
            'status',
            'created_at',
            'organizer_details',
            'participant_details',
            'event_details'
        ]

    def get_organizer_details(self, obj):
        """Детали организатора"""
        try:
            profile = TelegramProfile.objects.get(user=obj.organizer)
            return {
                'telegram_id': profile.telegram_id,
                'username': profile.telegram_username,
                'name': f"{profile.first_name} {profile.last_name}".strip()
            }
        except TelegramProfile.DoesNotExist:
            return None

    def get_participant_details(self, obj):
        """Детали участника"""
        try:
            profile = TelegramProfile.objects.get(user=obj.participant)
            return {
                'telegram_id': profile.telegram_id,
                'username': profile.telegram_username,
                'name': f"{profile.first_name} {profile.last_name}".strip()
            }
        except TelegramProfile.DoesNotExist:
            return None

    def get_event_details(self, obj):
        """Детали события"""
        return {
            'name': obj.event.name,
            'date': obj.event.date,
            'time': obj.event.time,
            'is_public': obj.event.is_public
        }


class PublicEventSerializer(serializers.ModelSerializer):
    """Сериализатор только для публичных событий"""
    owner = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id',
            'name',
            'date',
            'time',
            'details',
            'owner'
        ]

    def get_owner(self, obj):
        """Кто создал событие (только публичная информация)"""
        try:
            profile = TelegramProfile.objects.get(telegram_id=obj.user)
            return {
                'username': profile.telegram_username,
                'name': profile.first_name
            }
        except TelegramProfile.DoesNotExist:
            return {'username': None, 'name': 'Неизвестный'}