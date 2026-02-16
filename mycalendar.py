import psycopg2
from psycopg2 import sql


class Calendar:
    def __init__(self, db_config):
        """
        Инициализация с параметрами подключения к БД
        db_config = {
            'host': 'localhost',
            'database': 'botcalendar',
            'user': 'botuser',
            'password': 'secure_password'
        }
        """
        self.db_config = db_config

    def _get_connection(self):
        """Внутренний метод для получения подключения к БД"""
        return psycopg2.connect(**self.db_config)

    # CREATE - создание события
    def create_event(self, event_name, event_date, event_time, event_details):
        """Добавляет новое событие в базу данных"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO events (name, date, time, details)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (event_name, event_date, event_time, event_details))

            event_id = cursor.fetchone()[0]
            conn.commit()
            print(f"✅ Событие '{event_name}' создано с ID: {event_id}")
            return event_id

        except Exception as e:
            conn.rollback()
            print(f"❌ Ошибка при создании события: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    # READ - чтение одного события по ID
    def read_event(self, event_id):
        """Возвращает событие по его ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, date, time, details
                FROM events
                WHERE id = %s;
            """, (event_id,))

            row = cursor.fetchone()
            if row:
                event = {
                    'id': row[0],
                    'name': row[1],
                    'date': row[2],
                    'time': row[3],
                    'details': row[4]
                }
                return event
            else:
                print(f"Событие с ID {event_id} не найдено")
                return None

        except Exception as e:
            print(f"❌ Ошибка при чтении события: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    # EDIT - редактирование события
    def edit_event(self, event_id, **kwargs):
        """
        Редактирует поля события.
        kwargs может содержать: name, date, time, details
        """
        if not kwargs:
            print("Не указаны поля для обновления")
            return None

        conn = self._get_connection()
        cursor = conn.cursor()

        # Формируем SET часть запроса динамически
        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        values = list(kwargs.values()) + [event_id]

        try:
            query = sql.SQL("""
                UPDATE events
                SET {}
                WHERE id = %s
                RETURNING id;
            """).format(sql.SQL(set_clause))

            cursor.execute(query, values)
            updated_id = cursor.fetchone()

            if updated_id:
                conn.commit()
                print(f"✅ Событие ID {event_id} обновлено")
                return event_id
            else:
                print(f"Событие с ID {event_id} не найдено")
                return None

        except Exception as e:
            conn.rollback()
            print(f"❌ Ошибка при редактировании: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    # DELETE - удаление события
    def delete_event(self, event_id):
        """Удаляет событие по ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM events
                WHERE id = %s
                RETURNING id;
            """, (event_id,))

            deleted_id = cursor.fetchone()
            if deleted_id:
                conn.commit()
                print(f"✅ Событие ID {event_id} удалено")
                return event_id
            else:
                print(f"Событие с ID {event_id} не найдено")
                return None

        except Exception as e:
            conn.rollback()
            print(f"❌ Ошибка при удалении: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    # DISPLAY ALL - показать все события
    def display_events(self):
        """Возвращает список всех событий"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, date, time, details
                FROM events
                ORDER BY date, time;
            """)

            rows = cursor.fetchall()
            events = []

            if not rows:
                print("📭 Список событий пуст")
                return events

            print("\n=== 📅 ВСЕ СОБЫТИЯ ===")
            for row in rows:
                event = {
                    'id': row[0],
                    'name': row[1],
                    'date': row[2],
                    'time': row[3],
                    'details': row[4]
                }
                events.append(event)

                print(f"\nID: {event['id']}")
                print(f"  📌 Название: {event['name']}")
                print(f"  📆 Дата: {event['date']}")
                print(f"  ⏰ Время: {event['time']}")
                print(f"  📝 Детали: {event['details']}")
            print("========================")

            return events

        except Exception as e:
            print(f"❌ Ошибка при получении списка: {e}")
            return []
        finally:
            cursor.close()
            conn.close()