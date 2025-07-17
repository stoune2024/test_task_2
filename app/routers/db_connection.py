import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from app.config import settings

"""

Данный модуль используется для создания БД "users" и подключения к ней.

"""

# dialect+driver://username:password@host:port/database

# Устанавливаем соединение с postgres
connection = psycopg2.connect(
    user=f"{settings.postgres_user}",
    password=f"{settings.postgres_password}"
)
connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

# Создаем курсор для выполнения операций с базой данных
cursor = connection.cursor()

# Создаем базу данных
sql_create_database = cursor.execute(f'create database {settings.postgres_db_name}')

# Закрываем соединение
cursor.close()
connection.close()