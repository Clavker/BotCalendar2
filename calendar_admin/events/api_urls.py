from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'events', api_views.EventViewSet)
router.register(r'profiles', api_views.TelegramProfileViewSet)
router.register(r'appointments', api_views.AppointmentViewSet)

urlpatterns = [
    # Основные API через router
    path('', include(router.urls)),

    # Дополнительные endpoints
    path('user/<int:telegram_id>/events/', api_views.UserEventsView.as_view(),
         name='user-events'),
    path('statistics/', api_views.StatisticsView.as_view(), name='statistics'),

    # Аутентификация (базовая, можно расширить)
    path('api-auth/', include('rest_framework.urls')),
]