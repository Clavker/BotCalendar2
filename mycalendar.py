import psycopg2
from psycopg2 import sql


class Calendar:
    def __init__(self, db_config):
        self.db_config = db_config

    def _get_connection(self):
        return psycopg2.connect(**self.db_config)

    # CREATE - создание события для конкретного пользователя
    def create_event(self, user_id, event_name, event_date, event_time,
                     event_details):
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO events (user_id, name, date, time, details)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, (user_id, event_name, event_date, event_time, event_details))

            event_id = cursor.fetchone()[0]
            conn.commit()
            print(
                f"✅ Событие '{event_name}' создано для user {user_id} с ID: {event_id}")
            return event_id

        except Exception as e:
            conn.rollback()
            print(f"❌ Ошибка при создании события: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    # READ - чтение события (только если принадлежит пользователю)
    def read_event(self, user_id, event_id):
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, date, time, details
                FROM events
                WHERE id = %s AND user_id = %s;
            """, (event_id, user_id))

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
                print(
                    f"Событие с ID {event_id} не найдено или не принадлежит пользователю")
                return None

        except Exception as e:
            print(f"❌ Ошибка при чтении события: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    # EDIT - редактирование события (только если принадлежит пользователю)
    def edit_event(self, user_id, event_id, **kwargs):
        if not kwargs:
            print("Не указаны поля для обновления")
            return None

        conn = self._get_connection()
        cursor = conn.cursor()

        # Формируем SET часть запроса динамически
        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        values = list(kwargs.values()) + [event_id, user_id]

        try:
            query = sql.SQL("""
                UPDATE events
                SET {}
                WHERE id = %s AND user_id = %s
                RETURNING id;
            """).format(sql.SQL(set_clause))

            cursor.execute(query, values)
            updated_id = cursor.fetchone()

            if updated_id:
                conn.commit()
                print(f"✅ Событие ID {event_id} обновлено для user {user_id}")
                return event_id
            else:
                print(
                    f"Событие с ID {event_id} не найдено или не принадлежит пользователю")
                return None

        except Exception as e:
            conn.rollback()
            print(f"❌ Ошибка при редактировании: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    # DELETE - удаление события (только если принадлежит пользователю)
    def delete_event(self, user_id, event_id):
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM events
                WHERE id = %s AND user_id = %s
                RETURNING id;
            """, (event_id, user_id))

            deleted_id = cursor.fetchone()
            if deleted_id:
                conn.commit()
                print(f"✅ Событие ID {event_id} удалено для user {user_id}")
                return event_id
            else:
                print(
                    f"Событие с ID {event_id} не найдено или не принадлежит пользователю")
                return None

        except Exception as e:
            conn.rollback()
            print(f"❌ Ошибка при удалении: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    # DISPLAY ALL - показать все события пользователя
    def display_events(self, user_id):
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, name, date, time, details
                FROM events
                WHERE user_id = %s
                ORDER BY date, time;
            """, (user_id,))

            rows = cursor.fetchall()
            events = []

            if not rows:
                print(f"📭 Список событий для user {user_id} пуст")
                return events

            print(f"\n=== 📅 СОБЫТИЯ ПОЛЬЗОВАТЕЛЯ {user_id} ===")
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

    # Регистрация пользователя (если нужна)
    def register_user(self, user_id, username=None, first_name=None,
                      last_name=None):
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
                RETURNING user_id;
            """, (user_id, username, first_name, last_name))

            registered = cursor.fetchone()
            conn.commit()

            if registered:
                print(f"✅ Пользователь {user_id} зарегистрирован")
                return True
            else:
                print(f"ℹ️ Пользователь {user_id} уже существует")
                return False

        except Exception as e:
            conn.rollback()
            print(f"❌ Ошибка при регистрации: {e}")
            return False
        finally:
            cursor.close()
            conn.close()