import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from app.config import settings

"""

Данный модуль используется для создания БД "users" и подключения к ней.

"""

def create_database():
    connection = psycopg2.connect(
        user=f"{settings.postgres_user}",
        password=f"{settings.postgres_password}",
        host=f"{settings.docker_postgres_host}"
    )
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()
    sql_create_database = cursor.execute(f'create database {settings.postgres_db_name}')
    cursor.close()
    connection.close()