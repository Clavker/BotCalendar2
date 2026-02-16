import psycopg2

# Параметры подключения (замени на свои)
conn = psycopg2.connect(
    host="localhost",
    database="botcalendar",
    user="postgres",  # или botuser, если создавал
    password="твой_пароль"
)

# Создаем курсор
cursor = conn.cursor()

# Создаем таблицу
cursor.execute("""
CREATE TABLE events (
    id serial PRIMARY KEY,
    name text NOT NULL,
    date date NOT NULL,
    time time NOT NULL
);
""")

# Сохраняем изменения
conn.commit()

# Закрываем соединение
cursor.close()
conn.close()

print("Таблица events успешно создана!")