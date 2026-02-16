import os
import datetime


class Calendar:
    def __init__(self):
        self.events = {}  # Словарь для хранения событий

    # CREATE - создание события
    def create_event(self, event_name, event_date, event_time, event_details):
        event_id = len(self.events) + 1
        event = {
            "id": event_id,
            "name": event_name,
            "date": event_date,
            "time": event_time,
            "details": event_details
        }
        self.events[event_id] = event
        print(f"Событие '{event_name}' создано с ID: {event_id}")
        return event_id

    # READ - чтение одного события по ID
    def read_event(self, event_id):
        if event_id in self.events:
            event = self.events[event_id]
            print(f"\nСобытие ID: {event['id']}")
            print(f"Название: {event['name']}")
            print(f"Дата: {event['date']}")
            print(f"Время: {event['time']}")
            print(f"Детали: {event['details']}")
            return event
        else:
            print(f"Событие с ID {event_id} не найдено")
            return None

    # EDIT - редактирование события
    def edit_event(self, event_id, **kwargs):
        """
        kwargs может содержать: name, date, time, details
        Пример вызова: edit_event(1, name="Новое название", date="2024-01-01")
        """
        if event_id in self.events:
            event = self.events[event_id]
            # Обновляем только переданные поля
            if 'name' in kwargs:
                event['name'] = kwargs['name']
            if 'date' in kwargs:
                event['date'] = kwargs['date']
            if 'time' in kwargs:
                event['time'] = kwargs['time']
            if 'details' in kwargs:
                event['details'] = kwargs['details']

            print(f"Событие ID {event_id} обновлено")
            return event
        else:
            print(f"Событие с ID {event_id} не найдено")
            return None

    # DELETE - удаление события
    def delete_event(self, event_id):
        if event_id in self.events:
            deleted_event = self.events.pop(event_id)
            print(
                f"Событие '{deleted_event['name']}' (ID: {event_id}) удалено")
            return deleted_event
        else:
            print(f"Событие с ID {event_id} не найдено")
            return None

    # DISPLAY ALL - показать все события
    def display_events(self):
        if not self.events:
            print("Список событий пуст")
            return

        print("\n=== ВСЕ СОБЫТИЯ ===")
        for event_id, event in self.events.items():
            print(f"\nID: {event_id}")
            print(f"  Название: {event['name']}")
            print(f"  Дата: {event['date']}")
            print(f"  Время: {event['time']}")
            print(f"  Детали: {event['details']}")
        print("===================")